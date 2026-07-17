"""Test EM unconstraining trên tập giả lập có SỰ THẬT (true λ đã biết)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from ai_service import unconstraining as U

def test_em_recovers_lambda():
    rng = np.random.default_rng(0)
    true_lam = 12.0; N = 3000; cap = 10
    D = rng.poisson(true_lam, size=N)              # nhu cầu THẬT
    censored = D > cap                             # ngày bị cắt (hết chỗ)
    obs = np.minimum(D, cap).astype(float)         # chỉ quan sát tới cap
    lam, d = U._em_group(obs, censored)
    print(f"true λ={true_lam} | quan sát TB={obs.mean():.2f} (thấp hơn) | EM λ={lam:.2f} | impute TB={d.mean():.2f}")
    assert abs(lam - true_lam) / true_lam < 0.15, "EM phải khôi phục λ trong ~15%"
    assert d.mean() > obs.mean(), "impute phải kéo lên trên số quan sát bị cắt"
    assert abs(d.mean() - true_lam) < abs(obs.mean() - true_lam), "impute gần sự thật hơn số bán thô"

def test_unconstrain_frame():
    rng = np.random.default_rng(1)
    rows = []
    for od in range(5):
        lam = 8 + od * 3
        for _ in range(300):
            D = rng.poisson(lam); cap = 12
            b = min(D, cap); so = max(D - cap, 0)
            # mô phỏng search log ĐẾM THIẾU: chỉ thấy ~40% số bị từ chối
            so_seen = int(so * 0.4)
            rows.append(dict(od_id=od, is_tet=0, is_holiday=0, bookings=b, soldout=so_seen, true=D))
    h = pd.DataFrame(rows)
    out = U.unconstrain(h)
    obs = (h.bookings + h.soldout).sum(); unc = out.demand_unconstrained.sum(); true = h.true.sum()
    print(f"tổng thật={true} | quan sát (bán+soldout thấy)={obs} | EM={unc:.0f}")
    assert unc > obs, "EM phải bù phần cầu ẩn mà search log đếm thiếu"
    assert abs(unc - true) < abs(obs - true), "EM gần sự thật hơn số quan sát"
    print("OK")

if __name__ == "__main__":
    test_em_recovers_lambda(); test_unconstrain_frame(); print("PASS test_unconstraining")
