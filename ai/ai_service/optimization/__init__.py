"""KHỐI 2 — Tối ưu phân bổ chỗ.

Lớp A (DLP, `dlp.py`): xây ma trận ràng buộc a_ℓj / sức chứa c_ℓ -> giải LP tối đa hóa
doanh thu bằng HiGHS -> trích biến đối ngẫu làm bid price π_ℓ.
Quy tắc chấp nhận + quota (`acceptance.py`): f_j ≥ Σπ, làm tròn quota.
Lớp B: gán ghế bằng interval partitioning (`seat_assignment.py`) + ghép đoạn trống
bằng best-fit (`gap_combination.py`).

Module này là mặt tiền (facade) — re-export toàn bộ hàm từ các file con để nơi gọi chỉ
cần `from ai_service import optimization as opt` như trước khi tách file, không đổi gì
ở call site.
"""

from __future__ import annotations

from .. import config as C
from .acceptance import (
    check_acceptance,
    compute_accept_decisions,
    compute_quotas,
    round_quota,
)
from .dlp import (
    DLPInputs,
    build_capacity_matrix,
    build_demand_bounds,
    compute_segment_load,
    extract_bid_prices,
    solve_lp,
    validate_solution,
)
from .gap_combination import (
    _best_fit,
    _extract_free_intervals,
    find_gap_combinations,
)
from .seat_assignment import assign_seats, max_overlap

__all__ = [
    "DLPInputs",
    "build_capacity_matrix",
    "build_demand_bounds",
    "solve_lp",
    "extract_bid_prices",
    "validate_solution",
    "compute_segment_load",
    "check_acceptance",
    "compute_accept_decisions",
    "compute_quotas",
    "round_quota",
    "solve_bid_prices",
    "assign_seats",
    "max_overlap",
    "find_gap_combinations",
]


def solve_bid_prices(
    od_products, lambda_hat: dict[int, float], nseg: int, capacity: dict[str, int] = C.CAPACITY
) -> dict:
    """Pipeline đầy đủ Lớp A: ma trận -> LP -> giải HiGHS -> kiểm định -> bid price +
    quota + quy tắc chấp nhận. Đây là API công khai mà ai_service/app.py gọi.

    Trả về: bid_prices[(seg,seat_type)] -> π_ℓ, quotas[od_id] -> x_j (số thực),
    accept[od_id] -> {opportunity_cost, accept}, segment_load[(seg,seat_type)] -> tải
    0..1, revenue_lp (doanh thu tối ưu LP).
    """
    dlp = build_capacity_matrix(od_products, nseg, capacity)
    ub = build_demand_bounds(od_products, lambda_hat)

    res = solve_lp(dlp.fares, dlp.A, dlp.capacity, ub)
    validate_solution(res, dlp.A, dlp.capacity, ub)

    bid_prices = extract_bid_prices(res, dlp.constraint_keys)
    quotas = compute_quotas(od_products, res.x)
    accept = compute_accept_decisions(od_products, bid_prices)
    segment_load = compute_segment_load(od_products, res.x, dlp.constraint_keys, dlp.capacity)

    return dict(
        bid_prices=bid_prices,
        quotas=quotas,
        accept=accept,
        segment_load=segment_load,
        revenue_lp=float(dlp.fares @ res.x),
    )
