"""KHỐI 3 — Định giá động.

Ước lượng độ co giãn giá–cầu (ε cho mô hình nhân / α cho mô hình cộng) bằng hồi quy
2SLS với biến công cụ Hausman để xử lý nội sinh giá (giá và cầu cùng bị chi phối bởi
một sốc cầu không quan sát được — ví dụ người bán tăng giá khi thấy dấu hiệu cầu tăng
— khiến hồi quy OLS thường lệch). Sau đó định giá = markup trên chi phí cơ hội (bid
price). AI chỉ trả giá thô + diễn giải; ép trần/sàn là việc của backend (Policy Guard).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

from . import config as C

# ============================================================
# AI-09 — Chuẩn bị dữ liệu giá–lượng
# ============================================================

PRICE_QTY_COLUMNS = [
    "od_id",
    "seat_type",
    "dow",
    "month",
    "is_holiday",
    "is_tet",
    "distance_km",
    "shown_price",
    "willing",
]


def prepare_price_quantity_data(history: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn bị dữ liệu (giá, lượng) từ lịch sử thô cho hồi quy co giãn.

    Dùng `willing` (số khách sẵn sàng mua tại `shown_price`, suy ra từ willingness-to-
    pay của toàn bộ lượt tìm kiếm) làm biến lượng — KHÔNG dùng `bookings`, vì bookings
    bị kiểm duyệt bởi sức chứa còn trống (booked = min(willing, cap_left)): khi cháy
    vé, bookings phẳng ở mức capacity bất kể giá đổi thế nào, làm co giãn ước lượng
    được kéo méo về 0.
    """
    missing = [c for c in PRICE_QTY_COLUMNS if c not in history.columns]
    if missing:
        raise ValueError(f"history thiếu cột bắt buộc cho ước lượng co giãn: {missing}")

    df = history[PRICE_QTY_COLUMNS].copy()
    df = df[(df["shown_price"] > 0) & (df["willing"] >= 0)]
    df = df.dropna(subset=["shown_price", "willing"])
    return df.reset_index(drop=True)


# ============================================================
# AI-15.2 — Hồi quy OLS/2SLS thuần (numpy) + biến công cụ Hausman
# ============================================================


@dataclass(frozen=True)
class OLSResult:
    """Kết quả hồi quy OLS tối giản — đủ để kiểm định (se, t-stat, p-value, R²)."""

    beta: np.ndarray
    se: np.ndarray
    t_stats: np.ndarray
    r2: float
    n: int
    dof: int

    @property
    def p_values(self) -> np.ndarray:
        return 2 * stats.t.sf(np.abs(self.t_stats), self.dof)


def _ols_with_stats(X: np.ndarray, y: np.ndarray) -> OLSResult:
    """Hồi quy OLS bằng đại số tuyến tính thuần (không thêm dependency statsmodels
    chỉ cho vài hồi quy nhỏ). X phải đã có cột hằng số (intercept) ở vị trí đầu."""
    n, k = X.shape
    beta, _residuals, _rank, _sv = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    dof = max(n - k, 1)
    sigma2 = float(resid @ resid) / dof
    xtx_inv = np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.clip(np.diag(sigma2 * xtx_inv), 0, None))
    t_stats = np.divide(beta, se, out=np.full_like(beta, np.nan), where=se > 0)
    ss_res = float(resid @ resid)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return OLSResult(beta=beta, se=se, t_stats=t_stats, r2=r2, n=n, dof=dof)


def _leave_one_out_instrument(df: pd.DataFrame, group_cols: list[str], value_col: str) -> np.ndarray:
    """Biến công cụ Hausman: giá trung bình cùng nhóm (vd cùng OD), LOẠI TRỪ chính
    quan sát đang xét, dùng làm biến công cụ cho giá của quan sát đó.

    Vì đây là trung bình trên nhiều ngày khác, nó phản ánh mức giá hệ thống của
    nhóm (base_price, chính sách markup trung bình) chứ không phải sốc cầu riêng của
    đúng ngày đang xét — thỏa điều kiện liên quan (correlated với giá) và độc lập
    tương đối với nhiễu ngày đó (miễn các sốc cầu theo ngày không tự tương quan mạnh),
    nên xử lý được vấn đề nội sinh (giá phản ứng ngược lại theo cầu quan sát được).
    """
    grp = df.groupby(group_cols)[value_col]
    count = grp.transform("count")
    total = grp.transform("sum")
    denom = (count - 1).clip(lower=1)
    return ((total - df[value_col]) / denom).to_numpy(dtype=float)


def _two_stage_least_squares(
    endogenous: np.ndarray, instrument: np.ndarray, controls: np.ndarray, y: np.ndarray
) -> tuple[OLSResult, OLSResult]:
    """2SLS thủ công:
    Stage 1 — hồi quy biến nội sinh (giá hoặc log giá) theo biến công cụ + control,
    lấy giá trị DỰ ĐOÁN (phần biến thiên "ngoại sinh" của giá, đã lọc bỏ phần tương
    quan với nhiễu hồi quy ở Stage 2).
    Stage 2 — hồi quy y theo giá trị dự đoán đó + control. Hệ số thu được không còn bị
    thiên lệch do nội sinh, miễn biến công cụ thỏa exclusion restriction.
    """
    n = len(y)
    ones = np.ones((n, 1))
    instrument = instrument.reshape(-1, 1)
    X1 = np.hstack([ones, instrument, controls]) if controls.size else np.hstack([ones, instrument])
    stage1 = _ols_with_stats(X1, endogenous)
    fitted = X1 @ stage1.beta

    fitted = fitted.reshape(-1, 1)
    X2 = np.hstack([ones, fitted, controls]) if controls.size else np.hstack([ones, fitted])
    stage2 = _ols_with_stats(X2, y)
    return stage1, stage2


# ============================================================
# AI-15.1 + AI-15.3 — Ước lượng ε (mô hình nhân) / α (mô hình cộng) theo phân khúc
# ============================================================


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


# ============================================================
# AI-11 + AI-16.1 + AI-16.2 — Markup trên chi phí cơ hội + diễn giải
# ============================================================


def compute_opportunity_cost(od: dict, bid_prices: dict[tuple[int, str], float]) -> float:
    """c_j = Σ_ℓ a_ℓj·π_ℓ — tổng bid price các chặng mà OD j đi qua (chi phí cơ hội
    của việc bán 1 vé cho luồng OD j)."""
    stype = od["seat_type"]
    return sum(bid_prices.get((seg, stype), 0.0) for seg in od["segments"])


def markup_multiplicative(opportunity_cost: float, epsilon: float) -> float:
    """Công thức markup nhân cho cầu co giãn hằng số (constant elasticity demand):
    p* = c_j · ε/(ε−1). Chỉ có nghĩa khi ε > 1 (cầu co giãn đủ mạnh để tồn tại mức giá
    tối đa hóa lợi nhuận hữu hạn) — `config.ELASTICITY_FLOOR` đã đảm bảo ε ước lượng
    được luôn > 1, nhưng vẫn kiểm tra ở đây để an toàn khi hàm được gọi trực tiếp với
    giá trị ε tùy ý."""
    if opportunity_cost <= 0:
        return 0.0
    if epsilon <= 1.0:
        raise ValueError(f"epsilon phải > 1 để công thức markup nhân có nghĩa, nhận {epsilon}")
    return opportunity_cost * epsilon / (epsilon - 1)


def build_explanation(
    od: dict,
    bid_prices: dict[tuple[int, str], float],
    epsilon: float,
    segment_load: dict[tuple[int, str], float] | None = None,
) -> dict:
    """Sinh diễn giải cho một mức giá đề xuất: chặng nút cổ chai (bid price cao nhất
    trong các chặng OD đi qua), bid price từng chặng, và tải (% sức chứa đã phân bổ)
    tại chặng nút cổ chai đó — giúp người dùng hiểu VÌ SAO giá cao/thấp."""
    stype = od["seat_type"]
    seg_pis = {seg: bid_prices.get((seg, stype), 0.0) for seg in od["segments"]}
    bottleneck = max(seg_pis, key=seg_pis.get) if seg_pis else None

    bottleneck_load_pct = None
    if segment_load is not None and bottleneck is not None:
        load = segment_load.get((bottleneck, stype))
        if load is not None:
            bottleneck_load_pct = round(float(load) * 100, 1)

    return dict(
        bottleneck_segment=(int(bottleneck) if bottleneck is not None else None),
        segment_pi={int(k): float(v) for k, v in seg_pis.items()},
        bottleneck_load_pct=bottleneck_load_pct,
        elasticity=float(round(epsilon, 3)),
        base_price=float(od["base_price"]),
    )


def price_od(
    od: dict,
    bid_prices: dict[tuple[int, str], float],
    eps: dict[str, float],
    policy: dict | None = None,
    segment_load: dict[tuple[int, str], float] | None = None,
) -> dict:
    """od: dict (od_id, seat_type, segments, base_price). bid_prices: dict
    (seg,seat_type)->π. eps: dict seat_type->ε. segment_load: dict (seg,seat_type)->
    tải 0..1 (tùy chọn, để diễn giải). Trả về giá đề xuất + diễn giải."""
    stype = od["seat_type"]
    oc = compute_opportunity_cost(od, bid_prices)
    e = eps.get(stype, C.ELASTICITY[stype])

    markup_price = markup_multiplicative(oc, e) if oc > 0 else 0.0
    # sàn mềm = base_price (không bán dưới giá cơ sở)
    proposed = max(markup_price, od["base_price"])
    # trần surge (Policy Guard cứng ở tầng AI trước khi backend áp policy riêng)
    proposed = min(proposed, od["base_price"] * C.MAX_SURGE)

    final = proposed
    decision = "accepted"
    if policy:  # backend guard (tùy chọn)
        final = min(max(proposed, policy["min_price"]), policy["max_price"])
        if final != proposed:
            decision = "blocked"

    return dict(
        od_id=int(od["od_id"]),
        seat_type=stype,
        opportunity_cost=float(round(oc, 0)),
        proposed_price=float(round(proposed, 0)),
        final_price=float(round(final, 0)),
        decision=decision,
        explanation=build_explanation(od, bid_prices, e, segment_load),
    )
