"""Cấu hình mạng & tham số sinh dữ liệu — CỐ ĐỊNH 20 GA.
Neo theo số liệu đường sắt Bắc–Nam thật (xem Luat_Sinh_Du_Lieu_SRRM.md).
"""

from __future__ import annotations

# ---- 20 ga (Bắc -> Nam): (code, tên, km từ Hà Nội, pop độ hút, is_hub) ----
STATIONS = [
    ("HN", "Hà Nội", 0, 1.00, True),
    ("PLY", "Phủ Lý", 56, 0.25, False),
    ("NDI", "Nam Định", 87, 0.40, False),
    ("NBI", "Ninh Bình", 115, 0.30, False),
    ("THO", "Thanh Hóa", 175, 0.50, False),
    ("VIN", "Vinh", 319, 0.50, True),
    ("DHO", "Đồng Hới", 522, 0.30, False),
    ("DHA", "Đông Hà", 622, 0.25, False),
    ("HUE", "Huế", 688, 0.60, True),
    ("DNA", "Đà Nẵng", 791, 0.90, True),
    ("TKY", "Tam Kỳ", 865, 0.25, False),
    ("QNG", "Quảng Ngãi", 928, 0.35, False),
    ("DTR", "Diêu Trì (Quy Nhơn)", 1096, 0.45, False),
    ("THO2", "Tuy Hòa", 1198, 0.30, False),
    ("NTR", "Nha Trang", 1315, 0.70, True),
    ("TCH", "Tháp Chàm", 1408, 0.25, False),
    ("BTH", "Bình Thuận", 1551, 0.30, False),
    ("LKH", "Long Khánh", 1637, 0.20, False),
    ("BHO", "Biên Hòa", 1694, 0.40, False),
    ("SGN", "Sài Gòn", 1726, 1.00, True),
]

SEAT_TYPES = ["ngoi_mem", "giuong_nam_k6"]

# Sức chứa mỗi chặng theo loại chỗ (cấu hình toa thật)
CAPACITY = {"ngoi_mem": 192, "giuong_nam_k6": 252}  # 3x64 ; 6x42

# Giá cơ sở: phí cố định + đơn giá/km (neo theo giá SE1 thật)
FIXED_FARE = 20_000
PRICE_PER_KM = {"ngoi_mem": 670, "giuong_nam_k6": 760}

# Độ co giãn giá (cho định giá & mô phỏng WTP). eps>1
ELASTICITY = {"ngoi_mem": 1.8, "giuong_nam_k6": 1.6}
ELASTICITY_FLOOR, ELASTICITY_CAP = 1.5, 3.0  # chặn markup nổ khi ε→1
MAX_SURGE = 2.5  # trần giá động = 2.5× giá cơ sở (Policy Guard)

# ---- Hệ số nhu cầu ----
DOW_FACTOR = {0: 0.85, 1: 0.80, 2: 0.85, 3: 1.10, 4: 1.45, 5: 1.20, 6: 1.50}  # T2..CN (Mon=0)
DISTANCE_DECAY = 800.0  # exp(-dist/800)
PAIR_BOOST_HN_VIN = 1.6
BOTTLENECK_BOOST = 1.5  # OD đi qua chặng Huế–Đà Nẵng
SCALE_K = 54.0  # hằng số quy mô -> tải TB ~0.65 capacity tại nút cổ chai (đã hiệu chỉnh)

NEGBINOM_R = 12.0  # nhiễu nhẹ (thiên hướng học)
WTP_MEDIAN_MULT = 1.15
WTP_SIGMA_LOG = 0.25

BOOKING_HORIZON = 60  # ngày mở bán trước khi chạy
CANCEL_RATE = 0.07
BROWSE_MULT = 1.7  # lượt browsing (found, không mua) so với mua

# OD mở bán: ít nhất một đầu là hub, HOẶC base_od >= ngưỡng
MIN_BASE_OD = 0.5

HUE_IDX = 8  # index ga Huế
DNA_IDX = 9  # index ga Đà Nẵng  -> chặng nút cổ chai = segment giữa 8 và 9


def station_df():
    import pandas as pd

    rows = [dict(idx=i, code=c, name=n, km=k, pop=p, is_hub=h) for i, (c, n, k, p, h) in enumerate(STATIONS)]
    return pd.DataFrame(rows)


def season_factor(month: int, dest_idx: int) -> float:
    """Hè (6-8) tăng cho OD tới Đà Nẵng/Nha Trang; thấp điểm 2-4 giảm."""
    tourist = dest_idx in (DNA_IDX, 14)  # Đà Nẵng, Nha Trang
    if month in (6, 7, 8):
        return 1.35 if tourist else 1.0
    if month in (2, 3, 4):
        return 0.85
    return 1.0


def base_price(seat_type: str, distance_km: float) -> float:
    return FIXED_FARE + PRICE_PER_KM[seat_type] * distance_km
