"""AI-09 — Chuẩn bị dữ liệu giá–lượng cho hồi quy co giãn."""

from __future__ import annotations

import pandas as pd

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
