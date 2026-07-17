"""KHỐI 2 — Tối ưu phân bổ chỗ.
A) DLP (scipy HiGHS) -> bid price (biến đối ngẫu) + quota.
B) Gán ghế (interval partitioning) + ghép đoạn trống (best-fit).
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import linprog

from . import config as C


def solve_bid_prices(od_products, lambda_hat, nseg, capacity=C.CAPACITY):
    """DLP: max Σ f_j x_j  s.t.  Σ a_ℓj x_j ≤ c_ℓ (mỗi seg,seat_type);  0≤x_j≤λ̂_j.
    Trả về bid_prices[(seg,seat_type)], quotas[od_id], accept threshold.
    od_products: list dict có od_id, seat_type, segments, base_price.
    lambda_hat: dict od_id -> λ̂.
    """
    n = len(od_products)
    fares = np.array([od["base_price"] for od in od_products], float)
    ub = np.array([max(lambda_hat.get(od["od_id"], 0.0), 0.0) for od in od_products], float)

    # ràng buộc: mỗi (seg, seat_type) có ít nhất 1 OD
    cons = []  # (seg, stype)
    for stype in C.SEAT_TYPES:
        for seg in range(nseg):
            cons.append((seg, stype))
    con_index = {c: i for i, c in enumerate(cons)}
    A = np.zeros((len(cons), n))
    b = np.zeros(len(cons))
    for i, (seg, stype) in enumerate(cons):
        b[i] = capacity[stype]
    for j, od in enumerate(od_products):
        for seg in od["segments"]:
            A[con_index[(seg, od["seat_type"])], j] = 1.0

    res = linprog(-fares, A_ub=A, b_ub=b, bounds=[(0, u) for u in ub], method="highs")
    if not res.success:
        raise RuntimeError("DLP failed: " + res.message)

    # bid price = -dual của ràng buộc ≤ (giá trị biên của capacity)
    duals = np.asarray(res.ineqlin.marginals, float)
    pi = np.clip(-duals, 0, None)
    bid_prices = {cons[i]: float(pi[i]) for i in range(len(cons))}
    quotas = {od_products[j]["od_id"]: float(res.x[j]) for j in range(n)}

    # opportunity_cost & quyết định chấp nhận theo bid price
    accept = {}
    for od in od_products:
        oc = sum(bid_prices[(seg, od["seat_type"])] for seg in od["segments"])
        accept[od["od_id"]] = dict(opportunity_cost=oc, accept=bool(od["base_price"] >= oc))
    return dict(bid_prices=bid_prices, quotas=quotas, accept=accept, revenue_lp=float(fares @ res.x))


# ---------- Gán ghế: interval partitioning ----------
def assign_seats(bookings):
    """bookings: list dict (origin_idx, dest_idx, seat_type).
    Trả về seat_plan[seat_type] = list ghế, mỗi ghế = list booking [o,d).
    Số ghế dùng = tải chồng lấn cực đại (tối ưu)."""
    plans = {}
    for stype in C.SEAT_TYPES:
        items = sorted([b for b in bookings if b["seat_type"] == stype], key=lambda b: (b["origin_idx"], b["dest_idx"]))
        seats = []  # mỗi seat: (free_from, list booking)
        for b in items:
            placed = False
            for s in seats:
                if s["free_from"] <= b["origin_idx"]:  # ghế rảnh tại ga lên
                    s["book"].append(b)
                    s["free_from"] = b["dest_idx"]
                    placed = True
                    break
            if not placed:
                seats.append(dict(free_from=b["dest_idx"], book=[b]))
        plans[stype] = seats
    return plans


def max_overlap(bookings, stype, nseg):
    load = np.zeros(nseg)
    for b in bookings:
        if b["seat_type"] == stype:
            for seg in range(b["origin_idx"], b["dest_idx"]):
                load[seg] += 1
    return int(load.max()) if len(load) else 0


# ---------- Ghép đoạn trống ----------
def find_gap_combinations(seat_plan, sellable_ods, nstations):
    """Tìm khoảng trống trong từng ghế và gợi ý OD bán bù (best-fit).
    sellable_ods: list dict (od_id, origin_idx, dest_idx, seat_type)."""
    by_type = {}
    for od in sellable_ods:
        by_type.setdefault(od["seat_type"], []).append(od)
    gaps = []
    for stype, seats in seat_plan.items():
        for si, s in enumerate(seats):
            occ = sorted(s["book"], key=lambda b: b["origin_idx"])
            # khoảng trống = [0,ga đầu), giữa các booking, (ga cuối, N)
            cursor = 0
            free = []
            for b in occ:
                if b["origin_idx"] > cursor:
                    free.append((cursor, b["origin_idx"]))
                cursor = max(cursor, b["dest_idx"])
            if cursor < nstations - 1:
                free.append((cursor, nstations - 1))
            for a, z in free:
                if z - a < 1:
                    continue
                # best-fit: OD nằm gọn trong [a,z], dài nhất
                cands = [od for od in by_type.get(stype, []) if od["origin_idx"] >= a and od["dest_idx"] <= z]
                if cands:
                    best = max(cands, key=lambda od: od["dest_idx"] - od["origin_idx"])
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
