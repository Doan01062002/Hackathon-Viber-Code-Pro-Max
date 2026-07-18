"""AIEngine — facade thuần Python cho Khối 1 (forecast), 2 (optimize), 3 (price).

Thay cho ai_service/app.py (FastAPI) đã bỏ: backend import trực tiếp class này thay vì
gọi HTTP. Hợp đồng dữ liệu vẫn là các model Pydantic trong schemas.py — Pydantic độc lập
với FastAPI nên giữ nguyên được.

State (model đã train, elasticity, cache nghiệm tối ưu) là thuộc tính instance, thay cho
dict STATE toàn cục mà lifespan của FastAPI từng nạp.

Lưu ý cho phía gọi: các method ở đây là *đồng bộ* và nặng CPU (LightGBM predict, giải LP
bằng HiGHS). Trước đây FastAPI tự đẩy endpoint `def` sang threadpool; giờ không còn ai làm
hộ, nên code async phải tự bọc bằng `asyncio.to_thread(...)` để không chặn event loop.
"""

from __future__ import annotations

import hashlib
import os
import pickle
import threading
import time
import uuid
from datetime import date

import pandas as pd

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
    PriceExplanation,
    PriceRequest,
    PriceResponse,
    Quota,
)

# engine.py nằm ở ai/src/ai_service/ nên phải lùi 3 cấp mới tới ai/ (chứa models/).
_AI_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(_AI_ROOT, "models", "model.pkl")


class AIEngineError(RuntimeError):
    """Lỗi gốc của engine. Controller backend map sang HTTP status tương ứng."""


class InvalidRequestError(AIEngineError):
    """Tham số đầu vào sai định dạng — tương đương HTTP 422."""


class ODNotFoundError(AIEngineError):
    """Không tìm thấy od_id — tương đương HTTP 404."""


class ModelNotReadyError(AIEngineError):
    """Chưa nạp được model dự báo — tương đương HTTP 503."""


def parse_service_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise InvalidRequestError("service_date phai dung dinh dang ISO YYYY-MM-DD") from exc


def feature_rows(ods, service_date: date) -> pd.DataFrame:
    """Dựng ma trận đặc trưng cho forecaster từ một danh sách OD bất kỳ.

    Để ở mức module (không phải method) vì backend/optimize_service.py gọi với tập OD đã
    lọc theo database, không phải toàn bộ mạng của engine.
    """
    _, is_holiday, is_tet = datagen.calendar_factor(service_date)
    days_to_tet, is_pre_tet, is_post_tet, _ = datagen.tet_context(service_date)
    is_rainy, promo = datagen.weather_promo(service_date)
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
                "days_to_tet": days_to_tet,
                "is_pre_tet": int(is_pre_tet),
                "is_post_tet": int(is_post_tet),
                "is_rainy": int(is_rainy),
                "promo": int(promo),
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


def _lambda_fingerprint(demand: dict[int, float]) -> str:
    payload = "|".join(f"{od_id}:{value:.8f}" for od_id, value in sorted(demand.items()))
    return hashlib.sha256(payload.encode()).hexdigest()


class AIEngine:
    def __init__(self, model_path: str | None = MODEL_PATH):
        stations, segments, od_products, bottleneck = datagen.build_network()
        self.meta = {
            "stations": stations,
            "segments": segments,
            "od_products": od_products,
            "bottleneck_seg": bottleneck,
        }
        self.ods = {od["od_id"]: od for od in od_products}
        self.forecaster = None
        self.eps = C.ELASTICITY.copy()
        self._opt_cache: dict[str, dict] = {}
        # Backend gọi engine qua asyncio.to_thread nên nhiều thread có thể cùng vào
        # _optimize; khóa lại để không giải trùng cùng một ngày.
        self._lock = threading.Lock()

        if model_path and os.path.exists(model_path):
            with open(model_path, "rb") as model_file:
                bundle = pickle.load(model_file)
            self.forecaster = bundle["forecaster"]
            self.eps = bundle["eps"]

    # --- hạ tầng ---

    def health(self) -> dict:
        return {
            "status": "ok",
            "n_od": len(self.ods),
            "forecast_model_ready": self.forecaster is not None,
        }

    def _require_forecaster(self):
        if self.forecaster is None:
            raise ModelNotReadyError("forecast model chua san sang")
        return self.forecaster

    def _feature_rows(self, service_date: date) -> pd.DataFrame:
        return feature_rows(self.meta["od_products"], service_date)

    # --- Khối 1: dự báo nhu cầu ---

    def forecast(self, req: ForecastRequest) -> ForecastResponse:
        forecaster = self._require_forecaster()
        service_date = parse_service_date(req.service_date)
        stations = self.meta["stations"]
        prediction = forecaster.predict(self._feature_rows(service_date))
        items = [
            ForecastItem(
                od_id=int(row.od_id),
                origin=stations.code[self.ods[row.od_id]["origin_idx"]],
                dest=stations.code[self.ods[row.od_id]["dest_idx"]],
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

    # --- Khối 2: tối ưu chặng (DLP) ---

    def _solve(self, service_date: date, force_resolve: bool = False) -> tuple[dict, bool]:
        forecaster = self._require_forecaster()
        key = service_date.isoformat()
        prediction = forecaster.predict(self._feature_rows(service_date))
        demand = dict(zip(prediction["od_id"], prediction["lambda_hat"], strict=True))
        fingerprint = _lambda_fingerprint(demand)

        with self._lock:
            cached = self._opt_cache.get(key)
            if not force_resolve and cached is not None and cached["fingerprint"] == fingerprint:
                return cached["solution"], True

            started_at = time.time()
            solution = opt.solve_bid_prices(self.meta["od_products"], demand, len(self.meta["segments"]))
            solution["solve_ms"] = (time.time() - started_at) * 1000
            solution["run_version"] = f"{key}-{uuid.uuid4().hex[:12]}"
            self._opt_cache[key] = {"fingerprint": fingerprint, "solution": solution}
            return solution, False

    def optimize(self, req: OptimizeRequest) -> OptimizeResponse:
        solution, warm_started = self._solve(parse_service_date(req.service_date), force_resolve=req.force_resolve)
        bid_prices = [
            BidPrice(segment_id=segment, seat_type=seat_type, bid_price=round(value, 0))
            for (segment, seat_type), value in solution["bid_prices"].items()
            if value > 0
        ]
        quotas = [
            Quota(
                origin_idx=self.ods[od_id]["origin_idx"],
                dest_idx=self.ods[od_id]["dest_idx"],
                seat_type=self.ods[od_id]["seat_type"],
                quota=round(value, 3),
            )
            for od_id, value in solution["quotas"].items()
            if value > 0
        ]
        rejected_count = sum(1 for item in solution["accept"].values() if not item["accept"])
        return OptimizeResponse(
            service_date=req.service_date,
            run_version=solution["run_version"],
            warm_started=warm_started,
            solve_ms=round(solution["solve_ms"], 1),
            revenue_lp=round(solution["revenue_lp"], 0),
            bid_prices=bid_prices,
            quotas=quotas,
            n_rejected=rejected_count,
            n_od=len(solution["accept"]),
        )

    # --- Khối 3: định giá ---

    def price(self, req: PriceRequest) -> PriceResponse:
        # Nhánh snapshot: backend đã có sẵn bid price trong DB, engine chỉ tính giá (stateless).
        if req.segments is not None:
            if req.seat_type is None or req.base_price is None:
                raise InvalidRequestError("seat_type va base_price la bat buoc khi gui snapshot")
            od = {
                "od_id": req.od_id,
                "seat_type": req.seat_type,
                "base_price": req.base_price,
                "segments": [segment.segment_id for segment in req.segments],
            }
            bid_prices = {(segment.segment_id, req.seat_type): segment.bid_price for segment in req.segments}
            return PriceResponse(**pricing.price_od(od, bid_prices, self.eps))

        # Nhánh tự giải: engine tự chạy Khối 2 cho ngày đó rồi định giá.
        if req.od_id not in self.ods:
            raise ODNotFoundError("od_id khong ton tai")
        solution, _warm_started = self._solve(parse_service_date(req.service_date))
        policy = None
        if req.min_price is not None and req.max_price is not None:
            policy = {"min_price": req.min_price, "max_price": req.max_price}
        result = pricing.price_od(
            self.ods[req.od_id],
            solution["bid_prices"],
            self.eps,
            policy,
            segment_load=solution.get("segment_load"),
        )
        return PriceResponse(
            od_id=result["od_id"],
            seat_type=result["seat_type"],
            opportunity_cost=result["opportunity_cost"],
            proposed_price=result["proposed_price"],
            final_price=result["final_price"],
            decision=result["decision"],
            explanation=PriceExplanation(**result["explanation"]),
        )

    def clear_cache(self) -> None:
        with self._lock:
            self._opt_cache.clear()


_engine: AIEngine | None = None
_engine_lock = threading.Lock()


def get_engine() -> AIEngine:
    """Singleton dùng chung — thay cho việc lifespan của FastAPI nạp STATE một lần."""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = AIEngine()
    return _engine
