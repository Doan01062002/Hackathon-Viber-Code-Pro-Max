"""AI-15.1 + AI-15.3 + AI-15.4 — Ước lượng ε (mô hình nhân) / α (mô hình cộng) theo
phân khúc, dùng 2SLS (regression.py) + kiểm định thống kê."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .. import config as C
from .data_prep import prepare_price_quantity_data
from .regression import _leave_one_out_instrument, _two_stage_least_squares


@dataclass(frozen=True)
class ElasticityEstimate:
    """Kết quả ước lượng co giãn cho một phân khúc, kèm số liệu kiểm định (AI-15.4)."""

    value: float
    se: float = float("nan")
    t_stat: float = float("nan")
    r2: float = float("nan")
    first_stage_r2: float = float("nan")
    n: int = 0
    used_fallback: bool = True
    reason: str | None = None
    controls: list[str] = field(default_factory=list)


_CONTROL_COLUMNS = ["dow", "is_holiday", "is_tet"]


def validate_elasticity_estimate(
    est: ElasticityEstimate, min_t_stat: float = 1.96, min_first_stage_r2: float = 0.01
) -> bool:
    """AI-15.4 — Kiểm định ước lượng có đáng tin để dùng thay config không:
    - Hệ số phải có ý nghĩa thống kê ở mức ~95% (|t| ≥ 1.96).
    - Biến công cụ đủ mạnh ở Stage 1 (R² không quá thấp — chặn weak instrument, một
      biến công cụ yếu khiến 2SLS kém ổn định hơn cả OLS thường).
    - Giá trị ước lượng phải nằm trong miền hợp lệ (ε/α > 1 — nếu không công thức
      markup không có nghĩa / vô cực).
    """
    if np.isnan(est.t_stat) or abs(est.t_stat) < min_t_stat:
        return False
    if not np.isnan(est.first_stage_r2) and est.first_stage_r2 < min_first_stage_r2:
        return False
    return est.value > 1.0


def _estimate_2sls(
    d: pd.DataFrame,
    *,
    endogenous_col: str,
    fallback: float,
    min_obs: int,
    sign: float = -1.0,
) -> ElasticityEstimate:
    """Lõi dùng chung cho cả ước lượng ε (endogenous_col='log_price') và α
    (endogenous_col='shown_price'): hồi quy log(willing) theo biến nội sinh (giá hoặc
    log giá) đã được công cụ hóa bằng `_leave_one_out_instrument`, cộng control lịch."""
    if len(d) < min_obs:
        return ElasticityEstimate(value=fallback, n=len(d), used_fallback=True, reason="insufficient_data")

    instrument_raw = _leave_one_out_instrument(d, ["od_id"], "shown_price")
    if endogenous_col == "log_price":
        instrument = np.log(np.clip(instrument_raw, 1e-6, None))
    else:
        instrument = instrument_raw

    controls = d[_CONTROL_COLUMNS].to_numpy(dtype=float)
    y = np.log(np.clip(d["willing"].to_numpy(dtype=float), 1e-6, None))
    endogenous = d[endogenous_col].to_numpy(dtype=float)

    stage1, stage2 = _two_stage_least_squares(endogenous, instrument, controls, y)

    raw_value = sign * stage2.beta[1]
    est = ElasticityEstimate(
        value=float(raw_value),
        se=float(stage2.se[1]),
        t_stat=float(sign * stage2.t_stats[1]),  # cùng chiều dấu với `value` (sign đã đổi dấu beta)
        r2=float(stage2.r2),
        first_stage_r2=float(stage1.r2),
        n=len(d),
        used_fallback=False,
        controls=list(_CONTROL_COLUMNS),
    )

    if not validate_elasticity_estimate(est):
        reason = "not_significant_or_weak_instrument" if raw_value > 1.0 else "out_of_valid_range"
        return ElasticityEstimate(
            value=fallback,
            se=est.se,
            t_stat=est.t_stat,
            r2=est.r2,
            first_stage_r2=est.first_stage_r2,
            n=est.n,
            used_fallback=True,
            reason=reason,
            controls=est.controls,
        )

    clipped = float(np.clip(raw_value, C.ELASTICITY_FLOOR, C.ELASTICITY_CAP))
    if clipped != raw_value:
        return ElasticityEstimate(
            value=clipped,
            se=est.se,
            t_stat=est.t_stat,
            r2=est.r2,
            first_stage_r2=est.first_stage_r2,
            n=est.n,
            used_fallback=False,
            reason="clipped_to_bounds",
            controls=est.controls,
        )
    return est


def estimate_elasticity_iv(data: pd.DataFrame, seat_type: str, min_obs: int = 300) -> ElasticityEstimate:
    """AI-15.1 (theo phân khúc = seat_type) + AI-15.2 (2SLS) + AI-15.3 (ε).

    Mô hình nhân — cầu co giãn hằng số: log(willing) = a − ε·log(price) + control.
    ε ước lượng bằng 2SLS (log giá công cụ hóa bởi giá trung bình leave-one-out cùng
    OD) để xử lý nội sinh, fallback về `config.ELASTICITY[seat_type]` nếu dữ liệu
    không đủ hoặc không qua kiểm định (AI-15.4).
    """
    d = data[(data["seat_type"] == seat_type) & (data["willing"] > 0)].copy()
    d["log_price"] = np.log(d["shown_price"])
    return _estimate_2sls(d, endogenous_col="log_price", fallback=C.ELASTICITY[seat_type], min_obs=min_obs, sign=-1.0)


def estimate_exponential_alpha_iv(data: pd.DataFrame, seat_type: str, min_obs: int = 300) -> ElasticityEstimate:
    """AI-15.1 + AI-15.2 + AI-15.3 (α) — mô hình cầu dạng mũ (cộng): dùng cho công
    thức markup cộng thay thế (`docs/prd_duong_sat.md` mục 7.3): D(p) = A·exp(−α·p),
    tức log(willing) = a − α·price + control (hồi quy trên giá GỐC, không log).
    Cùng cơ chế 2SLS/kiểm định như `estimate_elasticity_iv`, chỉ khác biến nội sinh.
    """
    d = data[(data["seat_type"] == seat_type) & (data["willing"] > 0)].copy()
    # fallback alpha: suy từ ε config quanh mức giá cơ sở trung bình của phân khúc — vì
    # ELASTICITY_FLOOR/CAP là bậc ε (không thứ nguyên); alpha có thứ nguyên 1/giá.
    avg_price = float(d["shown_price"].mean()) if len(d) else 1.0
    fallback_alpha = C.ELASTICITY[seat_type] / max(avg_price, 1.0)
    return _estimate_2sls(d, endogenous_col="shown_price", fallback=fallback_alpha, min_obs=min_obs, sign=-1.0)


def estimate_elasticity(history: pd.DataFrame) -> dict[str, float]:
    """API công khai dùng bởi `scripts/train.py` (đóng gói vào model.pkl) và các nơi
    khác cần ε mỗi seat_type — chuẩn bị dữ liệu rồi ước lượng 2SLS theo phân khúc."""
    data = prepare_price_quantity_data(history)
    return {stype: estimate_elasticity_iv(data, stype).value for stype in C.SEAT_TYPES}


def estimate_elasticity_detailed(history: pd.DataFrame) -> dict[str, ElasticityEstimate]:
    """Như `estimate_elasticity` nhưng trả đầy đủ ElasticityEstimate (se/t-stat/r2/
    used_fallback) — dùng cho báo cáo/kiểm định (AI-15.4), không chỉ giá trị cuối."""
    data = prepare_price_quantity_data(history)
    return {stype: estimate_elasticity_iv(data, stype) for stype in C.SEAT_TYPES}
