"""KHỐI 3 — Định giá động.

Ước lượng độ co giãn giá–cầu (ε cho mô hình nhân / α cho mô hình cộng) bằng hồi quy
2SLS với biến công cụ Hausman để xử lý nội sinh giá (giá và cầu cùng bị chi phối bởi
một sốc cầu không quan sát được — ví dụ người bán tăng giá khi thấy dấu hiệu cầu tăng
— khiến hồi quy OLS thường lệch). Sau đó định giá = markup trên chi phí cơ hội (bid
price). AI chỉ trả giá thô + diễn giải; ép trần/sàn là việc của backend (Policy Guard).

- `data_prep.py`   (AI-09):        chuẩn bị dữ liệu giá–lượng.
- `regression.py`  (AI-15.2):      OLS/2SLS thuần + biến công cụ Hausman.
- `elasticity.py`  (AI-15.1/.3/.4): ước lượng ε/α theo phân khúc + kiểm định.
- `markup.py`      (AI-11/16.1/.2): c_j = Σa·π, công thức markup, diễn giải.

Module này là mặt tiền (facade) — re-export toàn bộ hàm từ các file con để nơi gọi chỉ
cần `from ai_service import pricing` như trước khi tách file, không đổi gì ở call site.
"""

from __future__ import annotations

from .. import config as C
from .data_prep import PRICE_QTY_COLUMNS, prepare_price_quantity_data
from .elasticity import (
    ElasticityEstimate,
    estimate_elasticity,
    estimate_elasticity_detailed,
    estimate_elasticity_iv,
    estimate_exponential_alpha_iv,
    validate_elasticity_estimate,
    _estimate_2sls,
)
from .markup import build_explanation, compute_opportunity_cost, markup_multiplicative
from .regression import (
    OLSResult,
    _leave_one_out_instrument,
    _ols_with_stats,
    _two_stage_least_squares,
)

__all__ = [
    "PRICE_QTY_COLUMNS",
    "prepare_price_quantity_data",
    "OLSResult",
    "ElasticityEstimate",
    "validate_elasticity_estimate",
    "estimate_elasticity_iv",
    "estimate_exponential_alpha_iv",
    "estimate_elasticity",
    "estimate_elasticity_detailed",
    "compute_opportunity_cost",
    "markup_multiplicative",
    "build_explanation",
    "price_od",
]


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
