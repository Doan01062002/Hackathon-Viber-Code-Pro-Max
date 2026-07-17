"""Lớp A — DLP (Deterministic Linear Program) -> bid price.

Xây ma trận ràng buộc a_ℓj / sức chứa c_ℓ -> giải LP tối đa hóa doanh thu bằng HiGHS ->
trích biến đối ngẫu làm bid price π_ℓ -> kiểm định nghiệm.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog

from .. import config as C


@dataclass(frozen=True)
class DLPInputs:
    """Ma trận & vector mô tả bài toán LP: max f·x  s.t.  A x ≤ capacity, 0 ≤ x ≤ ub."""

    fares: np.ndarray  # f_j — giá vé cơ sở từng OD, mục tiêu Σ f_j·x_j
    A: np.ndarray  # a_ℓj — 1 nếu OD j đi qua chặng/loại-chỗ ℓ, ngược lại 0
    capacity: np.ndarray  # c_ℓ — sức chứa từng (chặng, loại chỗ), cùng thứ tự hàng với A
    constraint_keys: list[tuple[int, str]]  # (segment_idx, seat_type) ứng với từng hàng của A


def build_capacity_matrix(od_products, nseg: int, capacity: dict[str, int] = C.CAPACITY) -> DLPInputs:
    """Xây ma trận hệ số chặng-OD a_ℓj và vector sức chứa c_ℓ.

    Mỗi hàng của A ứng với một ràng buộc (chặng, loại chỗ); mỗi cột ứng với một OD
    product j. a_ℓj = 1 nếu luồng OD j đi qua chặng ℓ với đúng loại chỗ đó.
    """
    n = len(od_products)
    fares = np.array([od["base_price"] for od in od_products], dtype=float)

    constraint_keys = [(seg, stype) for stype in C.SEAT_TYPES for seg in range(nseg)]
    con_index = {key: i for i, key in enumerate(constraint_keys)}

    A = np.zeros((len(constraint_keys), n))
    b = np.array([capacity[stype] for (_seg, stype) in constraint_keys], dtype=float)
    for j, od in enumerate(od_products):
        for seg in od["segments"]:
            A[con_index[(seg, od["seat_type"])], j] = 1.0

    return DLPInputs(fares=fares, A=A, capacity=b, constraint_keys=constraint_keys)


def build_demand_bounds(od_products, lambda_hat: dict[int, float]) -> np.ndarray:
    """Trần nhu cầu λ̂_j cho từng biến x_j (ràng buộc 0 ≤ x_j ≤ λ̂_j). OD không có dự
    báo (chưa dự báo được / thưa dữ liệu) mặc định λ̂_j = 0 — không cấp quota."""
    return np.array([max(lambda_hat.get(od["od_id"], 0.0), 0.0) for od in od_products], dtype=float)


def solve_lp(fares: np.ndarray, A: np.ndarray, capacity: np.ndarray, upper_bounds: np.ndarray):
    """Giải LP max Σf_j·x_j  s.t. A·x ≤ capacity, 0 ≤ x ≤ upper_bounds.

    method="highs" ủy quyền cho bộ giải HiGHS (cùng bộ giải LP mà OR-Tools cũng dùng
    làm backend) — dùng qua scipy để tránh thêm dependency `ortools` nặng chỉ cho một
    bài LP nhỏ (≤ vài trăm biến với quy mô 1-3 tàu của MVP).
    """
    bounds = [(0, u) for u in upper_bounds]
    res = linprog(-fares, A_ub=A, b_ub=capacity, bounds=bounds, method="highs")
    if not res.success:
        raise RuntimeError(f"DLP failed: {res.message}")
    return res


def extract_bid_prices(res, constraint_keys: list[tuple[int, str]]) -> dict[tuple[int, str], float]:
    """π_ℓ = giá trị đối ngẫu (dual/shadow price) của ràng buộc sức chứa A·x ≤ c.

    scipy trả dual của ràng buộc "≤" dưới dạng `marginals` không dương (mục tiêu đưa
    vào solver là -f nên marginal ≤ 0); đổi dấu để có π_ℓ ≥ 0, rồi clip 0 để chặn
    nhiễu số học âm rất nhỏ từ bộ giải.
    """
    duals = np.asarray(res.ineqlin.marginals, dtype=float)
    pi = np.clip(-duals, 0, None)
    return {constraint_keys[i]: float(pi[i]) for i in range(len(constraint_keys))}


def validate_solution(res, A: np.ndarray, capacity: np.ndarray, upper_bounds: np.ndarray, tol: float = 1e-4) -> None:
    """Kiểm định nghiệm trước khi tin dùng làm bid price/quota — nếu solver trả nghiệm
    không khả thi (bug số học, ràng buộc build sai) thì phải fail sớm và rõ ràng thay
    vì âm thầm phát hành bid price sai cho nghiệp vụ."""
    x = np.asarray(res.x, dtype=float)
    if np.any(x < -tol):
        raise RuntimeError(f"Nghiệm DLP có x_j âm bất thường: min={x.min()}")
    if np.any(x > upper_bounds + tol):
        raise RuntimeError("Nghiệm DLP vượt trần nhu cầu λ̂_j — vi phạm ràng buộc nhu cầu")
    load = A @ x
    if np.any(load > capacity + tol):
        over = np.where(load > capacity + tol)[0]
        raise RuntimeError(f"Nghiệm DLP vượt sức chứa tại {len(over)} ràng buộc — vi phạm ràng buộc chặng")


def compute_segment_load(
    od_products, x: np.ndarray, constraint_keys: list[tuple[int, str]], capacity: np.ndarray
) -> dict[tuple[int, str], float]:
    """Tải (utilization) mỗi (chặng, loại chỗ) = tổng x_j được phân bổ qua chặng đó /
    sức chứa c_ℓ, tỉ lệ trong [0,1]. Dùng để diễn giải giá (Khối 3 — pricing.py):
    nút cổ chai càng đầy tải thì bid price càng đáng tin/càng dễ giải thích với người dùng."""
    load = dict.fromkeys(constraint_keys, 0.0)
    for j, od in enumerate(od_products):
        stype = od["seat_type"]
        xj = float(x[j])
        for seg in od["segments"]:
            load[(seg, stype)] = load.get((seg, stype), 0.0) + xj
    return {
        key: (load[key] / cap if cap > 0 else 0.0) for key, cap in zip(constraint_keys, capacity, strict=True)
    }
