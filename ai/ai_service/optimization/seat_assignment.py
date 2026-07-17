"""Lớp B — Gán ghế vật lý: interval partitioning.

Booking được mô hình hóa thành khoảng nửa-mở [origin_idx, dest_idx) trên trục ga —
hai booking dùng chung 1 ghế được nếu khoảng của chúng không giao nhau.
"""

from __future__ import annotations

import numpy as np

from .. import config as C


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
