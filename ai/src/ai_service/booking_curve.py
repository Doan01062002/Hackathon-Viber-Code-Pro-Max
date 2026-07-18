"""Booking curve / pickup — dự phóng nhu cầu CUỐI từ số đặt vé ĐANG có.

Khái niệm:
  • lead_time = số ngày trước khởi hành mà một vé được đặt.
  • Đường cong đặt vé c(τ) = tỉ lệ (trên tổng vé cuối cùng) đã đặt xong khi còn τ ngày.
    Tại τ = 0 (ngày chạy) c = 1; τ lớn (mở bán) c nhỏ. Đường cong tăng dần khi tới gần.
  • Pickup: đang còn τ ngày, đã có b vé -> dự phóng vé CUỐI = b / c(τ).
    Cầu "còn nhặt tiếp" (remaining pickup) = final − b.

Dùng để: (a) đưa tín hiệu "đặt sớm bất thường" vào cảnh báo cầu; (b) ước lượng cầu cuối
khi chưa tới ngày chạy, bổ trợ cho dự báo nền của Khối 1.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class BookingCurve:
    def __init__(self, horizon: int, curve: np.ndarray):
        self.horizon = int(horizon)
        self.curve = np.clip(np.asarray(curve, float), 1e-6, 1.0)   # index = days_to_go 0..H

    # ---- dùng ----
    def fraction(self, days_to_go: int) -> float:
        t = int(np.clip(days_to_go, 0, self.horizon))
        return float(self.curve[t])

    def project(self, current_bookings: float, days_to_go: int) -> float:
        """Dự phóng vé CUỐI từ số vé hiện có khi còn `days_to_go` ngày."""
        return float(current_bookings) / self.fraction(days_to_go)

    def remaining(self, current_bookings: float, days_to_go: int) -> float:
        return max(self.project(current_bookings, days_to_go) - current_bookings, 0.0)

    # ---- lưu/nạp gọn ----
    def to_dict(self):
        return {"horizon": self.horizon, "curve": self.curve.tolist()}

    @staticmethod
    def from_dict(d):
        return BookingCurve(d["horizon"], np.asarray(d["curve"], float))


def fit(bookings: pd.DataFrame, horizon: int = 60,
        trip_col: str = "trip_id", lead_col: str = "lead_time") -> BookingCurve:
    """Fit đường cong TRUNG BÌNH từ dữ liệu đặt vé thật.
    bookings cần cột [trip_col, lead_col]. Chuẩn hóa theo từng chuyến rồi lấy trung bình."""
    b = bookings[[trip_col, lead_col]].copy()
    b[lead_col] = b[lead_col].clip(0, horizon)
    taus = np.arange(horizon + 1)
    acc = np.zeros(horizon + 1)
    ntrip = 0
    for _, g in b.groupby(trip_col):
        leads = g[lead_col].values
        total = len(leads)
        if total == 0:
            continue
        # cum[τ] = tỉ lệ vé có lead >= τ (đã đặt khi còn τ ngày)
        cum = np.array([(leads >= t).mean() for t in taus])
        acc += cum
        ntrip += 1
    curve = acc / max(ntrip, 1)
    curve[0] = 1.0                          # τ=0 chắc chắn đã đặt hết
    curve = np.maximum.accumulate(curve[::-1])[::-1]   # ép đơn điệu giảm theo τ
    return BookingCurve(horizon, curve)


def fit_theoretical(horizon: int = 60, scale: float = 15.0) -> BookingCurve:
    """Đường cong lý thuyết khi mật độ đặt vé ∝ exp(−lead/scale) (đặt dồn về gần ngày chạy).
    Dùng khi chưa có lead_time thật (vd luồng datagen tổng hợp)."""
    taus = np.arange(horizon + 1)
    denom = 1.0 - np.exp(-horizon / scale)
    curve = (np.exp(-taus / scale) - np.exp(-horizon / scale)) / denom  # P(lead>=τ)
    curve[0] = 1.0
    return BookingCurve(horizon, curve)


def evaluate(bc: BookingCurve, bookings: pd.DataFrame, at_days: int = 14,
             trip_col: str = "trip_id", lead_col: str = "lead_time") -> dict:
    """Đo sai số pickup: đứng ở `at_days` ngày trước chạy, dự phóng vé cuối vs thực tế."""
    b = bookings[[trip_col, lead_col]].copy()
    errs = []
    for _, g in b.groupby(trip_col):
        leads = g[lead_col].values
        final = len(leads)
        if final < 5:
            continue
        so_far = int((leads >= at_days).sum())          # đã đặt tại thời điểm at_days
        if so_far == 0:
            continue
        proj = bc.project(so_far, at_days)
        errs.append(abs(proj - final) / final)
    return dict(at_days=at_days, n_trips=len(errs),
                pickup_mape=float(np.mean(errs) * 100) if errs else None)
