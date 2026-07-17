"""FastAPI ai-service — phơi 3 khối AI theo hợp đồng /internal/*.

Thiết kế: ai-service STATELESS về nghiệp vụ. Ở bản demo này, khi khởi động nó tự
sinh dữ liệu + huấn luyện mô hình để endpoint chạy được ngay. Khi triển khai thật,
backend đẩy snapshot dữ liệu vào payload thay vì ai-service tự sinh.
"""

from __future__ import annotations

import hashlib
import os
import pickle
import time
import uuid
from contextlib import asynccontextmanager
from datetime import date

import pandas as pd
from fastapi import FastAPI, HTTPException

from . import datagen, pricing
from . import optimization as opt

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "model.pkl")
from .schemas import (
    BidPrice,
    ForecastItem,
    ForecastRequest,
    ForecastResponse,
    OptimizeRequest,
    OptimizeResponse,
    PriceExplanation,
    PriceRequest,
    PriceResponse,
    Quota,
)

STATE = {}


def _iso(d: str) -> date:
    try:
        return date.fromisoformat(d)
    except ValueError as exc:
        raise HTTPException(422, f"service_date không hợp lệ (cần ISO 8601, vd '2024-02-11'): {d}") from exc


def _feature_rows(ods, d: date):
    _, is_hol, is_tet = datagen.calendar_factor(d)
    return pd.DataFrame(
        [
            dict(
                od_id=od["od_id"],
                seat_type=od["seat_type"],
                dow=d.weekday(),
                month=d.month,
                is_holiday=int(is_hol),
                is_tet=int(is_tet),
                is_summer=int(d.month in (6, 7, 8)),
                distance_km=od["distance_km"],
                base_price=od["base_price"],
                pop_o=od["pop_o"],
                pop_d=od["pop_d"],
                is_hub_o=int(od["is_hub_o"]),
                is_hub_d=int(od["is_hub_d"]),
                crosses_bottleneck=int(od["crosses_bottleneck"]),
            )
            for od in ods
        ]
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Mạng lưới (ga/chặng/OD) là tất định -> dựng lại từ config, không cần sinh dữ liệu.
    st, segs, ods, bn = datagen.build_network()
    STATE["meta"] = {"stations": st, "segments": segs, "od_products": ods, "bottleneck_seg": bn}
    STATE["ods"] = {od["od_id"]: od for od in ods}
    # Nạp model đã train sẵn (KHÔNG train lúc khởi động).
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"Chưa có model tại {MODEL_PATH}. Hãy chạy trước: python scripts/train.py")
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
    ods = STATE["meta"]["od_products"]
    st = STATE["meta"]["stations"]
    pred = STATE["forecaster"].predict(_feature_rows(ods, d))
    items = [
        ForecastItem(
            od_id=int(r.od_id),
            origin=st.code[STATE["ods"][r.od_id]["origin_idx"]],
            dest=st.code[STATE["ods"][r.od_id]["dest_idx"]],
            seat_type=r.seat_type,
            lambda_hat=round(float(r.lambda_hat), 3),
            p10=round(float(r.p10), 3),
            p50=round(float(r.p50), 3),
            p90=round(float(r.p90), 3),
        )
        for r in pred.itertuples()
    ]
    return ForecastResponse(service_date=req.service_date, model_version=STATE["forecaster"].version, items=items)


def _lambda_fingerprint(lam: dict) -> str:
    """Hash nhu cầu dự báo hiện tại — dùng để phát hiện input đổi giữa 2 lần resolve.
    Làm tròn 4 chữ số để tránh nhiễu số thực gây warm-start sai (coi là đổi trong khi
    thực chất không đổi)."""
    payload = repr(sorted((k, round(v, 4)) for k, v in lam.items()))
    return hashlib.md5(payload.encode()).hexdigest()


def _optimize(d: date, force_resolve: bool = False) -> tuple[dict, bool]:
    """Trả về (solution, warm_started). warm_started=True nghĩa là input (nhu cầu dự
    báo) không đổi so với lần giải gần nhất cho cùng service_date, nên tái dùng nguyên
    lời giải cũ thay vì giải lại DLP — đây là chiến lược warm-start ở mức MVP: bài
    toán đủ nhỏ (1-3 tàu) nên giải lại từ đầu khi có thay đổi vẫn đạt K7 (gần real-time)
    mà không cần warm-start basis thật của bộ giải LP (scipy HiGHS không hỗ trợ qua
    API công khai)."""
    key = d.isoformat()
    ods = STATE["meta"]["od_products"]
    nseg = len(STATE["meta"]["segments"])
    pred = STATE["forecaster"].predict(_feature_rows(ods, d))
    lam = dict(zip(pred["od_id"], pred["lambda_hat"]))
    fp = _lambda_fingerprint(lam)

    cached = STATE["opt_cache"].get(key)
    if not force_resolve and cached is not None and cached["fingerprint"] == fp:
        return cached["sol"], True

    t0 = time.time()
    sol = opt.solve_bid_prices(ods, lam, nseg)
    sol["solve_ms"] = (time.time() - t0) * 1000
    sol["run_version"] = f"{key}-{uuid.uuid4().hex[:12]}"
    STATE["opt_cache"][key] = {"fingerprint": fp, "sol": sol}
    return sol, False


@app.post("/internal/optimize", response_model=OptimizeResponse)
def optimize(req: OptimizeRequest):
    d = _iso(req.service_date)
    sol, warm_started = _optimize(d, force_resolve=req.force_resolve)
    bps = [
        BidPrice(segment_id=seg, seat_type=st, bid_price=round(v, 0))
        for (seg, st), v in sol["bid_prices"].items()
        if v > 0
    ]
    quotas = [
        Quota(
            origin_idx=STATE["ods"][od_id]["origin_idx"],
            dest_idx=STATE["ods"][od_id]["dest_idx"],
            seat_type=STATE["ods"][od_id]["seat_type"],
            quota=round(q, 3),
        )
        for od_id, q in sol["quotas"].items()
        if q > 0
    ]
    n_rej = sum(1 for a in sol["accept"].values() if not a["accept"])
    return OptimizeResponse(
        service_date=req.service_date,
        run_version=sol["run_version"],
        warm_started=warm_started,
        solve_ms=round(sol["solve_ms"], 1),
        revenue_lp=round(sol["revenue_lp"], 0),
        bid_prices=bps,
        quotas=quotas,
        n_rejected=n_rej,
        n_od=len(sol["accept"]),
    )


@app.post("/internal/price", response_model=PriceResponse)
def price(req: PriceRequest):
    if req.od_id not in STATE["ods"]:
        raise HTTPException(404, "od_id không tồn tại")
    d = _iso(req.service_date)
    sol, _warm_started = _optimize(d)
    od = STATE["ods"][req.od_id]
    policy = None
    if req.min_price is not None and req.max_price is not None:
        policy = {"min_price": req.min_price, "max_price": req.max_price}
    q = pricing.price_od(od, sol["bid_prices"], STATE["eps"], policy, segment_load=sol.get("segment_load"))
    return PriceResponse(
        od_id=q["od_id"],
        seat_type=q["seat_type"],
        opportunity_cost=q["opportunity_cost"],
        proposed_price=q["proposed_price"],
        final_price=q["final_price"],
        decision=q["decision"],
        explanation=PriceExplanation(**q["explanation"]),
    )
