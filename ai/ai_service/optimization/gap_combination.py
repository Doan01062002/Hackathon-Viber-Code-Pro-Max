"""Lớp B — Ghép đoạn trống (gap combinations): best-fit."""

from __future__ import annotations


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
