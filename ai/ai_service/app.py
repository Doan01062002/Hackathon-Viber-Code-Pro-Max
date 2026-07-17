"""FastAPI ai-service — phơi 3 khối AI theo hợp đồng /internal/*.

Thiết kế: ai-service STATELESS về nghiệp vụ. Ở bản demo này, khi khởi động nó tự
sinh dữ liệu + huấn luyện mô hình để endpoint chạy được ngay. Khi triển khai thật,
backend đẩy snapshot dữ liệu vào payload thay vì ai-service tự sinh.
"""
from __future__ import annotations
import os
import time
import pickle
from datetime import date
from contextlib import asynccontextmanager
import pandas as pd
from fastapi import FastAPI, HTTPException

from . import datagen, forecasting, optimization as opt, pricing, config as C

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "models", "model.pkl")
from .schemas import (ForecastRequest, ForecastResponse, ForecastItem,
                      OptimizeRequest, OptimizeResponse, BidPrice,
                      PriceRequest, PriceResponse)

STATE = {}


def _iso(d: str) -> date:
    return date.fromisoformat(d)


def _feature_rows(ods, d: date):
    _, is_hol, is_tet = datagen.calendar_factor(d)
    return pd.DataFrame([dict(
        od_id=od["od_id"], seat_type=od["seat_type"], dow=d.weekday(), month=d.month,
        is_holiday=int(is_hol), is_tet=int(is_tet), is_summer=int(d.month in (6, 7, 8)),
        distance_km=od["distance_km"], base_price=od["base_price"],
        pop_o=od["pop_o"], pop_d=od["pop_d"],
        is_hub_o=int(od["is_hub_o"]), is_hub_d=int(od["is_hub_d"]),
        crosses_bottleneck=int(od["crosses_bottleneck"])) for od in ods])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Mạng lưới (ga/chặng/OD) là tất định -> dựng lại từ config, không cần sinh dữ liệu.
    st, segs, ods, bn = datagen.build_network()
    STATE["meta"] = {"stations": st, "segments": segs, "od_products": ods, "bottleneck_seg": bn}
    STATE["ods"] = {od["od_id"]: od for od in ods}
    # Nạp model đã train sẵn (KHÔNG train lúc khởi động).
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(
            f"Chưa có model tại {MODEL_PATH}. Hãy chạy trước: python scripts/train.py")
    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)
    STATE["forecaster"] = bundle["forecaster"]
    STATE["eps"] = bundle["eps"]
    STATE["opt_cache"] = {}
    yield
    STATE.clear()


app = FastAPI(title="SRRM ai-service", version="1.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "n_od": len(STATE.get("ods", {}))}


@app.post("/internal/forecast", response_model=ForecastResponse)
def forecast(req: ForecastRequest):
    d = _iso(req.service_date)
    ods = STATE["meta"]["od_products"]; st = STATE["meta"]["stations"]
    pred = STATE["forecaster"].predict(_feature_rows(ods, d))
    items = [ForecastItem(od_id=int(r.od_id), origin=st.code[STATE["ods"][r.od_id]["origin_idx"]],
                          dest=st.code[STATE["ods"][r.od_id]["dest_idx"]], seat_type=r.seat_type,
                          lambda_hat=round(float(r.lambda_hat), 3), p10=round(float(r.p10), 3),
                          p50=round(float(r.p50), 3), p90=round(float(r.p90), 3))
             for r in pred.itertuples()]
    return ForecastResponse(service_date=req.service_date,
                            model_version=STATE["forecaster"].version, items=items)


def _optimize(d: date):
    key = d.isoformat()
    if key in STATE["opt_cache"]:
        return STATE["opt_cache"][key]
    ods = STATE["meta"]["od_products"]; nseg = len(STATE["meta"]["segments"])
    pred = STATE["forecaster"].predict(_feature_rows(ods, d))
    lam = dict(zip(pred["od_id"], pred["lambda_hat"]))
    t0 = time.time()
    sol = opt.solve_bid_prices(ods, lam, nseg)
    sol["solve_ms"] = (time.time() - t0) * 1000
    STATE["opt_cache"][key] = sol
    return sol


@app.post("/internal/optimize", response_model=OptimizeResponse)
def optimize(req: OptimizeRequest):
    d = _iso(req.service_date)
    sol = _optimize(d)
    bps = [BidPrice(segment_id=seg, seat_type=st, bid_price=round(v, 0))
           for (seg, st), v in sol["bid_prices"].items() if v > 0]
    n_rej = sum(1 for a in sol["accept"].values() if not a["accept"])
    return OptimizeResponse(service_date=req.service_date, solve_ms=round(sol["solve_ms"], 1),
                            revenue_lp=round(sol["revenue_lp"], 0), bid_prices=bps,
                            n_rejected=n_rej, n_od=len(sol["accept"]))


@app.post("/internal/price", response_model=PriceResponse)
def price(req: PriceRequest):
    if req.od_id not in STATE["ods"]:
        raise HTTPException(404, "od_id không tồn tại")
    d = _iso(req.service_date)
    sol = _optimize(d)
    od = STATE["ods"][req.od_id]
    policy = None
    if req.min_price is not None and req.max_price is not None:
        policy = {"min_price": req.min_price, "max_price": req.max_price}
    q = pricing.price_od(od, sol["bid_prices"], STATE["eps"], policy)
    return PriceResponse(**q)
