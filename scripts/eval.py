"""Đánh giá model ĐÃ LƯU trên tập test — in các chỉ số CÓ Ý NGHĨA
(WAPE tổng hợp theo OD / theo ngày, độ phủ phân vị), thay vì chỉ WAPE dòng.

Chạy:  python scripts/eval.py --from-seeds out/seeds
       python scripts/eval.py                      # dùng datagen (có cả corr với λ thật)
"""
from __future__ import annotations
import sys, os, pickle, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import date
import numpy as np, pandas as pd
from ai_service import datagen, forecasting

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(REPO, "models", "model.pkl")


def load_hist(from_seeds):
    if from_seeds:
        from ai_service import adapter
        h = adapter.load_history(from_seeds)
    else:
        h = datagen.simulate(date(2023, 1, 1), 730, seed=7)["history"].copy()
    h["service_date"] = pd.to_datetime(h["service_date"])
    return h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-seeds", type=str, default=None)
    args = ap.parse_args()

    if not os.path.exists(MODEL_PATH):
        print("Chưa có model — chạy trước: python scripts/train.py"); return
    fc = pickle.load(open(MODEL_PATH, "rb"))["forecaster"]

    h = load_hist(args.from_seeds)
    dts = sorted(h["service_date"].unique())
    split = dts[int(len(dts) * 0.8)]
    test = h[h.service_date >= split].copy()
    test["target"] = test["bookings"] + test["soldout"]

    pred = fc.predict(test)
    test["pred"] = pred["lambda_hat"].values
    test["p10"] = pred["p10"].values; test["p90"] = pred["p90"].values; test["p50"] = pred["p50"].values

    def wape(a, p): return float(np.sum(np.abs(p - a)) / max(np.sum(a), 1e-9))

    row_wape = wape(test.target.values, test.pred.values)
    by_od = test.groupby("od_id").agg(a=("target", "sum"), p=("pred", "sum"))
    by_day = test.groupby("service_date").agg(a=("target", "sum"), p=("pred", "sum"))
    cov80 = float(((test.target >= test.p10) & (test.target <= test.p90)).mean())
    cov50 = float((test.target <= test.p50).mean())

    print(f"Tập test: {len(test):,} dòng | {test.od_id.nunique()} OD | "
          f"{test.service_date.nunique()} ngày (từ {split.date()})")
    print("\n=== CHỈ SỐ DỰ BÁO ===")
    print(f"  WAPE theo DÒNG (nhiễu đếm — tham khảo) : {row_wape*100:5.1f}%")
    print(f"  WAPE tổng hợp theo OD  (có ý nghĩa)    : {wape(by_od.a, by_od.p)*100:5.1f}%")
    print(f"  WAPE tổng hợp theo NGÀY (có ý nghĩa)   : {wape(by_day.a, by_day.p)*100:5.1f}%")
    print(f"  Độ phủ p10–p90 (kỳ vọng ~80%)          : {cov80*100:5.1f}%")
    print(f"  Tỉ lệ thực tế ≤ p50 (kỳ vọng ~50%)     : {cov50*100:5.1f}%")
    if "lambda_true" in test:
        print(f"  corr(λ̂, λ_thật)                        : {np.corrcoef(test.pred, test.lambda_true)[0,1]:.3f}")

    print("\n=== VÍ DỤ: tổng cầu test theo vài OD (thực tế vs dự báo) ===")
    ex = by_od.sort_values("a", ascending=False).head(6)
    for oid, r in ex.iterrows():
        print(f"  OD #{oid:3d}: thực tế {r.a:6.0f} | dự báo {r.p:6.0f} | lệch {100*(r.p-r.a)/max(r.a,1):+.1f}%")


if __name__ == "__main__":
    main()