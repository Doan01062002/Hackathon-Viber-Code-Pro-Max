"""Test booking curve/pickup trên dữ liệu giả lập có lead_time exp."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from ai_service import booking_curve as BC

def make(n_trips=400, scale=15.0, horizon=60, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for tr in range(n_trips):
        final = rng.integers(30, 120)
        leads = np.clip(rng.exponential(scale, size=final).astype(int), 0, horizon)
        for l in leads:
            rows.append(dict(trip_id=tr, lead_time=int(l)))
    return pd.DataFrame(rows)

def test_curve_and_pickup():
    df = make()
    bc = BC.fit(df, horizon=60)
    assert bc.fraction(0) == 1.0
    assert bc.fraction(60) < bc.fraction(5), "còn nhiều ngày -> đã đặt ít hơn"
    # đơn điệu giảm theo τ
    c = bc.curve
    assert np.all(np.diff(c) <= 1e-9), "curve phải giảm dần theo days_to_go"
    ev = BC.evaluate(bc, df, at_days=14)
    print(f"pickup MAPE @14 ngày = {ev['pickup_mape']:.1f}%  ({ev['n_trips']} chuyến)")
    assert ev["pickup_mape"] < 25, "pickup phải hợp lý (<25% MAPE)"
    # đường lý thuyết xấp xỉ đường fit
    bt = BC.fit_theoretical(60, 15.0)
    diff = np.mean(np.abs(bt.curve - bc.curve))
    print(f"lệch TB curve lý thuyết vs fit = {diff:.3f}")
    assert diff < 0.06
    print("OK")

if __name__ == "__main__":
    test_curve_and_pickup(); print("PASS test_booking_curve")
