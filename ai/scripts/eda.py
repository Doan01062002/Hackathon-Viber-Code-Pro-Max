"""EDA — Khám phá dữ liệu lịch sử + kiểm định feature set.

Kiểm tra schema/thiếu, thống kê mô tả nhu cầu theo OD, mùa vụ/lễ-Tết/thời tiết/khuyến mãi,
phân bố lead time (nếu có seeds), và KIỂM ĐỊNH các cột FEATURES của Khối 1.

Chạy:  python scripts/eda.py --from-seeds out/seeds
       python scripts/eda.py                       # dùng datagen
"""
from __future__ import annotations
import sys, os, warnings, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
warnings.filterwarnings("ignore")
from datetime import date
import numpy as np, pandas as pd
from ai_service import datagen, forecasting


def bar(x, scale=8):
    return "█" * int(max(x, 0) * scale)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-seeds", type=str, default=None)
    args = ap.parse_args()

    if args.from_seeds:
        from ai_service import adapter
        print(f"[EDA] Nạp 21 bảng từ {args.from_seeds} ...")
        h = adapter.load_history(args.from_seeds)
        src = "seeds"
    else:
        print("[EDA] Sinh dữ liệu bằng datagen (365 ngày) ...")
        h = datagen.simulate(date(2023, 1, 1), 365, seed=7)["history"].copy()
        src = "datagen"
    h["service_date"] = pd.to_datetime(h["service_date"])
    h["demand"] = h["bookings"] + h["soldout"]

    # ---------- 1) SCHEMA / MISSING ----------
    print(f"\n=== 1) SCHEMA & THIẾU DỮ LIỆU  (nguồn: {src}) ===")
    print(f"  {len(h):,} dòng · {h.od_id.nunique()} OD · {h.service_date.nunique()} ngày "
          f"({h.service_date.min().date()} → {h.service_date.max().date()})")
    miss = h.isna().sum()
    miss = miss[miss > 0]
    print("  Cột thiếu:", "KHÔNG (đã điền đủ lưới OD×ngày)" if miss.empty
          else dict(miss))

    # ---------- 2) THỐNG KÊ CẦU THEO OD ----------
    print("\n=== 2) NHU CẦU THEO OD ===")
    od = h.groupby("od_id").agg(cau_tb=("demand", "mean"), cau_tong=("demand", "sum"),
                                soldout=("soldout", "sum")).sort_values("cau_tong", ascending=False)
    print(f"  Cầu/ngày/OD: TB={h.demand.mean():.2f}  trung vị={h.demand.median():.0f}  "
          f"max={h.demand.max():.0f}")
    print(f"  Tỉ lệ dòng có sold_out (bị kiểm duyệt): {(h.soldout>0).mean()*100:.1f}%")
    print("  Top 5 OD theo tổng cầu:")
    for oid, r in od.head(5).iterrows():
        print(f"    OD #{int(oid):3d}: tổng {r.cau_tong:7.0f} | TB/ngày {r.cau_tb:5.1f} | soldout {r.soldout:5.0f}")

    # ---------- 3) MÙA VỤ / LỄ-TẾT / THỜI TIẾT / KHUYẾN MÃI ----------
    print("\n=== 3) MÙA VỤ & SỰ KIỆN ===")
    mo = h.groupby(h.service_date.dt.month)["demand"].mean()
    print("  Cầu TB theo tháng (đỉnh Tết tháng 1–2):")
    for m, v in mo.items():
        print(f"    T{m:2d}: {v:5.2f} {bar(v)}")
    dow = h.groupby("dow")["demand"].mean()
    names = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    print("  Cầu TB theo thứ:", " ".join(f"{names[d]}={v:.1f}" for d, v in dow.items()))
    for flag, lab in [("is_tet", "Tết"), ("is_holiday", "Lễ"), ("is_pre_tet", "Trước Tết (đi)"),
                      ("is_post_tet", "Sau Tết (về)"), ("is_rainy", "Mùa mưa"), ("promo", "Khuyến mãi")]:
        if flag in h and h[flag].sum() > 0:
            on = h.loc[h[flag] == 1, "demand"].mean(); off = h.loc[h[flag] == 0, "demand"].mean()
            print(f"  {lab:16s}: cầu TB {on:5.2f} vs thường {off:5.2f}  (×{on/max(off,1e-9):.2f})")

    # ---------- 4) LEAD TIME (nếu có seeds) ----------
    if args.from_seeds:
        try:
            from ai_service import adapter
            lt = adapter.load_bookings_leadtime(args.from_seeds)
            q = lt["lead_time"].quantile([.25, .5, .75, .9]).round(0).astype(int).to_dict()
            print("\n=== 4) LEAD TIME (ngày đặt trước khởi hành) ===")
            print(f"  n={len(lt):,} vé | TB={lt.lead_time.mean():.1f} | "
                  f"phân vị 25/50/75/90 = {q[0.25]}/{q[0.5]}/{q[0.75]}/{q[0.9]} ngày")
        except Exception as e:
            print(f"\n=== 4) LEAD TIME === (bỏ qua: {e})")

    # ---------- 5) KIỂM ĐỊNH FEATURE SET ----------
    print("\n=== 5) KIỂM ĐỊNH FEATURE SET (Khối 1) ===")
    d = forecasting._ensure(h)
    problems = []
    for c in forecasting.FEATURES:
        if c not in d:
            problems.append(f"{c}: THIẾU"); continue
        col = d[c]
        if col.isna().any():
            problems.append(f"{c}: có NaN ({col.isna().sum()})")
        if not np.issubdtype(col.dtype, np.number):
            problems.append(f"{c}: không phải số ({col.dtype})")
    print(f"  {len(forecasting.FEATURES)} đặc trưng: " +
          ("✅ hợp lệ (đủ cột, kiểu số, không NaN)" if not problems else "⚠ " + "; ".join(problems)))
    # tương quan với cầu (lọc feature vô ích)
    num = d[forecasting.FEATURES].copy(); num["demand"] = h["demand"].values
    corr = num.corr()["demand"].drop("demand").abs().sort_values(ascending=False)
    print("  |corr| cao nhất với cầu:", ", ".join(f"{k}={v:.2f}" for k, v in corr.head(6).items()))
    weak = corr[corr < 0.02]
    if len(weak):
        print("  (đặc trưng gần như không tương quan tuyến tính — vẫn có thể hữu ích phi tuyến:",
              ", ".join(weak.index), ")")

    print("\n[EDA] Xong.")


if __name__ == "__main__":
    main()
