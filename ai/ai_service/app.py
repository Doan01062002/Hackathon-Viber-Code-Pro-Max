from __future__ import annotations

import os
import pickle
import time
from contextlib import asynccontextmanager
from datetime import date

import pandas as pd
from fastapi import FastAPI, HTTPException

from . import config as C
from . import datagen, pricing
from . import optimization as opt
from .schemas import (
    BidPrice,
    ForecastItem,
    ForecastRequest,
    ForecastResponse,
    OptimizeRequest,
    OptimizeResponse,
    PriceRequest,
    PriceResponse,
)

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "model.pkl"
)
STATE: dict[str, object] = {}


def _iso(value: str) -> date:
    return date.fromisoformat(value)


def _feature_rows(ods, service_date: date) -> pd.DataFrame:
    _, is_holiday, is_tet = datagen.calendar_factor(service_date)
    return pd.DataFrame(
        [
            {
                "od_id": od["od_id"],
                "seat_type": od["seat_type"],
                "dow": service_date.weekday(),
                "month": service_date.month,
                "is_holiday": int(is_holiday),
                "is_tet": int(is_tet),
                "is_summer": int(service_date.month in (6, 7, 8)),
                "distance_km": od["distance_km"],
                "base_price": od["base_price"],
                "pop_o": od["pop_o"],
                "pop_d": od["pop_d"],
                "is_hub_o": int(od["is_hub_o"]),
                "is_hub_d": int(od["is_hub_d"]),
                "crosses_bottleneck": int(od["crosses_bottleneck"]),
            }
            for od in ods
        ]
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    stations, segments, od_products, bottleneck = datagen.build_network()
    STATE["meta"] = {
        "stations": stations,
        "segments": segments,
        "od_products": od_products,
        "bottleneck_seg": bottleneck,
    }
    STATE["ods"] = {od["od_id"]: od for od in od_products}
    STATE["forecaster"] = None
    STATE["eps"] = C.ELASTICITY.copy()
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as model_file:
            bundle = pickle.load(model_file)
        STATE["forecaster"] = bundle["forecaster"]
        STATE["eps"] = bundle["eps"]
    STATE["opt_cache"] = {}
    yield
    STATE.clear()


app = FastAPI(title="SRRM ai-service", version="1.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "n_od": len(STATE.get("ods", {})),
        "forecast_model_ready": STATE.get("forecaster") is not None,
    }


def _require_forecaster():
    forecaster = STATE.get("forecaster")
    if forecaster is None:
        raise HTTPException(503, "forecast model chua san sang")
    return forecaster


@app.post("/internal/forecast", response_model=ForecastResponse)
def forecast(req: ForecastRequest):
    forecaster = _require_forecaster()
    service_date = _iso(req.service_date)
    meta = STATE["meta"]
    ods = meta["od_products"]
    stations = meta["stations"]
    od_index = STATE["ods"]
    prediction = forecaster.predict(_feature_rows(ods, service_date))
    items = [
        ForecastItem(
            od_id=int(row.od_id),
            origin=stations.code[od_index[row.od_id]["origin_idx"]],
            dest=stations.code[od_index[row.od_id]["dest_idx"]],
            seat_type=row.seat_type,
            lambda_hat=round(float(row.lambda_hat), 3),
            p10=round(float(row.p10), 3),
            p50=round(float(row.p50), 3),
            p90=round(float(row.p90), 3),
        )
        for row in prediction.itertuples()
    ]
    return ForecastResponse(
        service_date=req.service_date,
        model_version=forecaster.version,
        items=items,
    )


def _optimize(service_date: date):
    forecaster = _require_forecaster()
    key = service_date.isoformat()
    cache = STATE["opt_cache"]
    if key in cache:
        return cache[key]
    meta = STATE["meta"]
    ods = meta["od_products"]
    prediction = forecaster.predict(_feature_rows(ods, service_date))
    demand = dict(zip(prediction["od_id"], prediction["lambda_hat"], strict=True))
    started_at = time.time()
    solution = opt.solve_bid_prices(ods, demand, len(meta["segments"]))
    solution["solve_ms"] = (time.time() - started_at) * 1000
    cache[key] = solution
    return solution


@app.post("/internal/optimize", response_model=OptimizeResponse)
def optimize(req: OptimizeRequest):
    solution = _optimize(_iso(req.service_date))
    bid_prices = [
        BidPrice(segment_id=segment, seat_type=seat_type, bid_price=round(value, 0))
        for (segment, seat_type), value in solution["bid_prices"].items()
        if value > 0
    ]
    rejected_count = sum(1 for item in solution["accept"].values() if not item["accept"])
    return OptimizeResponse(
        service_date=req.service_date,
        solve_ms=round(solution["solve_ms"], 1),
        revenue_lp=round(solution["revenue_lp"], 0),
        bid_prices=bid_prices,
        n_rejected=rejected_count,
        n_od=len(solution["accept"]),
    )


@app.post("/internal/price", response_model=PriceResponse)
def price(req: PriceRequest):
    if req.segments is not None:
        if req.seat_type is None or req.base_price is None:
            raise HTTPException(422, "seat_type va base_price la bat buoc khi gui snapshot")
        od = {
            "od_id": req.od_id,
            "seat_type": req.seat_type,
            "base_price": req.base_price,
            "segments": [segment.segment_id for segment in req.segments],
        }
        bid_prices = {
            (segment.segment_id, req.seat_type): segment.bid_price for segment in req.segments
        }
        return PriceResponse(
            **pricing.price_od(od, bid_prices, STATE.get("eps", C.ELASTICITY))
        )

    od_index = STATE.get("ods", {})
    if req.od_id not in od_index:
        raise HTTPException(404, "od_id khong ton tai")
    solution = _optimize(_iso(req.service_date))
    policy = None
    if req.min_price is not None and req.max_price is not None:
        policy = {"min_price": req.min_price, "max_price": req.max_price}
    result = pricing.price_od(
        od_index[req.od_id], solution["bid_prices"], STATE["eps"], policy
    )
    return PriceResponse(**result)
