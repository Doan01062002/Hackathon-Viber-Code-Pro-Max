"""KHỐI 2 — Tối ưu phân bổ chỗ.

Lớp A (DLP): xây ma trận ràng buộc a_ℓj / sức chứa c_ℓ -> giải LP tối đa hóa doanh thu
bằng HiGHS -> trích biến đối ngẫu làm bid price π_ℓ -> quy tắc chấp nhận + quota.

Lớp B (vật lý): gán ghế bằng interval partitioning (tối ưu, O(n·log n)) + ghép đoạn
trống bằng best-fit.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog

from . import config as C

# ============================================================
# Lớp A — DLP (Deterministic Linear Program) -> bid price + quota
# ============================================================


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


def solve_bid_prices(
    od_products, lambda_hat: dict[int, float], nseg: int, capacity: dict[str, int] = C.CAPACITY
) -> dict:
    """Pipeline đầy đủ Lớp A: ma trận -> LP -> giải HiGHS -> kiểm định -> bid price +
    quota + quy tắc chấp nhận. Đây là API công khai mà ai_service/app.py gọi.

    Trả về: bid_prices[(seg,seat_type)] -> π_ℓ, quotas[od_id] -> x_j (số thực),
    accept[od_id] -> {opportunity_cost, accept}, revenue_lp (doanh thu tối ưu LP).
    """
    dlp = build_capacity_matrix(od_products, nseg, capacity)
    ub = build_demand_bounds(od_products, lambda_hat)

    res = solve_lp(dlp.fares, dlp.A, dlp.capacity, ub)
    validate_solution(res, dlp.A, dlp.capacity, ub)

    bid_prices = extract_bid_prices(res, dlp.constraint_keys)
    quotas = compute_quotas(od_products, res.x)
    accept = compute_accept_decisions(od_products, bid_prices)

    return dict(
        bid_prices=bid_prices,
        quotas=quotas,
        accept=accept,
        revenue_lp=float(dlp.fares @ res.x),
    )


# ============================================================
# Lớp B — Gán ghế vật lý: interval partitioning
# ============================================================
# Booking được mô hình hóa thành khoảng nửa-mở [origin_idx, dest_idx) trên trục ga —
# hai booking dùng chung 1 ghế được nếu khoảng của chúng không giao nhau.


def assign_seats(bookings: list[dict], locked_seat_count: dict[str, int] | None = None) -> dict[str, list[dict]]:
    """Gán ghế vật lý giảm phân mảnh bằng interval partitioning (greedy theo booking
    sắp xếp theo (origin_idx, dest_idx)); số ghế thường dùng = tải chồng lấn cực đại
    — đây là kết quả tối ưu đã biết của bài toán interval graph coloring.

    bookings: list dict {origin_idx, dest_idx, seat_type} — mỗi booking là khoảng [o, d).
    locked_seat_count: số ghế bị khóa mỗi loại chỗ (dispatcher khóa cho đoàn thể/bảo
    trì/ưu tiên — xem docs/specs/user-roles.md). Ghế khóa được dựng sẵn trong seat_plan
    ở trạng thái "không nhận booking mới" (free_from=+inf) nên thuật toán không gán vé
    thường vào đó, nhưng vẫn được trả về để phía gọi biết tổng số ghế của toa.

    Trả về seat_plan[seat_type] = list ghế; mỗi ghế = {free_from, book: [...], locked?: bool}.
    """
    locked_seat_count = locked_seat_count or {}
    plans: dict[str, list[dict]] = {}
    for stype in C.SEAT_TYPES:
        items = sorted(
            (b for b in bookings if b["seat_type"] == stype),
            key=lambda b: (b["origin_idx"], b["dest_idx"]),
        )
        seats: list[dict] = [
            dict(free_from=float("inf"), book=[], locked=True) for _ in range(locked_seat_count.get(stype, 0))
        ]
        for b in items:
            placed = False
            for s in seats:
                if not s.get("locked") and s["free_from"] <= b["origin_idx"]:
                    s["book"].append(b)
                    s["free_from"] = b["dest_idx"]
                    placed = True
                    break
            if not placed:
                seats.append(dict(free_from=b["dest_idx"], book=[b]))
        plans[stype] = seats
    return plans


def max_overlap(bookings: list[dict], stype: str, nseg: int) -> int:
    """Tải chồng lấn cực đại của loại chỗ `stype` — số ghế thường (không tính ghế
    khóa) tối thiểu cần dùng để phục vụ hết các booking mà không chồng lấn. Dùng để
    kiểm nghiệm `assign_seats` có tối ưu không: số ghế thường đã dùng phải bằng đúng
    giá trị này."""
    load = np.zeros(nseg)
    for b in bookings:
        if b["seat_type"] == stype:
            for seg in range(b["origin_idx"], b["dest_idx"]):
                load[seg] += 1
    return int(load.max()) if len(load) else 0


# ============================================================
# Lớp B — Ghép đoạn trống (gap combinations): best-fit
# ============================================================


def _extract_free_intervals(seat: dict, nstations: int) -> list[tuple[int, int]]:
    """Trích các khoảng trống [a, z) của một ghế: trước booking đầu, giữa các booking
    liên tiếp, và sau booking cuối tới hết tuyến."""
    occ = sorted(seat["book"], key=lambda b: b["origin_idx"])
    cursor = 0
    free = []
    for b in occ:
        if b["origin_idx"] > cursor:
            free.append((cursor, b["origin_idx"]))
        cursor = max(cursor, b["dest_idx"])
    if cursor < nstations - 1:
        free.append((cursor, nstations - 1))
    return free


def _best_fit(gap: tuple[int, int], candidates: list[dict]) -> dict | None:
    """Trong các OD ứng viên nằm gọn trong khoảng trống `gap`, chọn OD dài nhất
    (best-fit: lấp đầy khoảng trống nhiều nhất, tối đa hóa doanh thu bù thêm)."""
    a, z = gap
    fits = [od for od in candidates if od["origin_idx"] >= a and od["dest_idx"] <= z]
    if not fits:
        return None
    return max(fits, key=lambda od: od["dest_idx"] - od["origin_idx"])


def find_gap_combinations(seat_plan: dict[str, list[dict]], sellable_ods: list[dict], nstations: int) -> list[dict]:
    """FR2.5 — quét mọi ghế, tìm khoảng trống giữa các booking, gợi ý OD bán bù
    (best-fit) để lấp khoảng trống đó.

    sellable_ods: list dict {od_id, origin_idx, dest_idx, seat_type} — các OD đang mở bán.
    Trả về list gợi ý {seat_type, seat_index, from_idx, to_idx, suggest_od_id, suggest_span}.
    """
    by_type: dict[str, list[dict]] = {}
    for od in sellable_ods:
        by_type.setdefault(od["seat_type"], []).append(od)

    gaps = []
    for stype, seats in seat_plan.items():
        candidates = by_type.get(stype, [])
        for si, seat in enumerate(seats):
            if seat.get("locked"):
                continue
            for a, z in _extract_free_intervals(seat, nstations):
                if z - a < 1:
                    continue
                best = _best_fit((a, z), candidates)
                if best is not None:
                    gaps.append(
                        dict(
                            seat_type=stype,
                            seat_index=si,
                            from_idx=a,
                            to_idx=z,
                            suggest_od_id=best["od_id"],
                            suggest_span=(best["origin_idx"], best["dest_idx"]),
                        )
                    )
    return gaps
