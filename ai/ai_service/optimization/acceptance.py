"""Quy tắc chấp nhận (FR2.2) + tính quota từ nghiệm DLP."""

from __future__ import annotations

import numpy as np


def check_acceptance(base_price: float, opportunity_cost: float) -> bool:
    """FR2.2 — chấp nhận yêu cầu vé OD j khi giá vé f_j ≥ Σ_ℓ a_ℓj·π_ℓ (giá vé không
    thấp hơn tổng chi phí cơ hội các chặng nó đi qua)."""
    return base_price >= opportunity_cost


def compute_accept_decisions(od_products, bid_prices: dict[tuple[int, str], float]) -> dict[int, dict]:
    """Với mỗi OD, tính chi phí cơ hội (tổng bid price các chặng đi qua) và quyết định
    chấp nhận/từ chối theo `check_acceptance`."""
    accept = {}
    for od in od_products:
        oc = sum(bid_prices.get((seg, od["seat_type"]), 0.0) for seg in od["segments"])
        accept[od["od_id"]] = dict(opportunity_cost=oc, accept=check_acceptance(od["base_price"], oc))
    return accept


def compute_quotas(od_products, x: np.ndarray) -> dict[int, float]:
    """Quota thô (số thực) của mỗi OD = nghiệm x_j của DLP — số vé tối ưu nên bán.
    Giữ dạng số thực ở đây (dùng tiếp cho lớp B / phân tích); làm tròn về số nguyên
    khi cần lưu trữ thì dùng `round_quota`."""
    return {od["od_id"]: max(float(x[j]), 0.0) for j, od in enumerate(od_products)}


def round_quota(raw_quota: float, tol: float = 1e-6) -> int:
    """Xử lý biên & làm tròn quota trước khi dùng làm số ghế thật (số nguyên):

    - Nhiễu số học âm rất nhỏ (vd -1e-9 do bộ giải LP) -> coi là 0, không phải quota âm thật.
    - Quota âm rõ ràng (vượt tolerance) -> lỗi dữ liệu, raise thay vì âm thầm ép về 0.
    - Làm tròn XUỐNG (floor), không làm tròn thông thường: quota là trần số vé được
      bán cho một luồng OD trong lời giải DLP — làm tròn lên có thể khiến tổng vé bán
      vượt sức chứa mà bài toán đã tối ưu (mỗi OD làm tròn lên 0.99 -> 1 ghế, cộng dồn
      nhiều OD trên cùng chặng có thể vượt c_ℓ).
    """
    if raw_quota < 0:
        if raw_quota < -tol:
            raise ValueError(f"Quota âm bất thường (không phải nhiễu số học): {raw_quota}")
        raw_quota = 0.0
    return int(np.floor(raw_quota + tol))
