"""HUẤN LUYỆN MỘT LẦN (MVP) — train mô hình + ước lượng co giãn rồi LƯU ra file.
App sẽ nạp file này thay vì train lúc khởi động.

Chạy:  python scripts/train.py
Sinh lại model mỗi khi dữ liệu thay đổi (chạy tay — MVP chưa cần train định kỳ).
"""
from __future__ import annotations
import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
from datetime import date
import pandas as pd
from ai_service import datagen, forecasting, pricing

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(REPO, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")

START, DAYS = date(2023, 1, 1), 730     # dùng khi sinh bằng datagen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-seeds", type=str, default=None,
                    help="thư mục 21 bảng CSV (vd out/seeds). Bỏ trống = tự sinh bằng datagen.")
    args = ap.parse_args()
    os.makedirs(MODEL_DIR, exist_ok=True)

    if args.from_seeds:
        from ai_service import adapter
        print(f"[train] Nạp dữ liệu THẬT từ 21 bảng: {args.from_seeds} ...")
        hist = adapter.load_history(args.from_seeds)
    else:
        print(f"[train] Tự sinh dữ liệu bằng datagen ({DAYS} ngày) ...")
        sim = datagen.simulate(START, DAYS, seed=7)
        hist = sim["history"].copy()
    hist["service_date"] = pd.to_datetime(hist["service_date"])

    # tách train/test theo thời gian (80/20)
    dts = sorted(hist["service_date"].unique())
    split = dts[int(len(dts) * 0.8)]
    train = hist[hist.service_date < split]
    test = hist[hist.service_date >= split]

    print(f"[train] Huấn luyện Forecaster (train {len(train):,} / test {len(test):,}) ...")
    fc = forecasting.Forecaster().fit(train)
    ev = forecasting.evaluate(fc, test)
    corr = ev.get("corr_lambda_true")
    corr_s = f"{corr:.3f}" if corr is not None else "n/a (data thật không có ground-truth)"
    print(f"[train] Backtest: WAPE={ev['wape']*100:.1f}%  corr(λ̂,λ_thật)={corr_s}")

    # train lại trên TOÀN BỘ dữ liệu để phục vụ (không giữ test riêng)
    fc_full = forecasting.Forecaster().fit(hist)
    eps = pricing.estimate_elasticity(hist)
    print(f"[train] Độ co giãn ước lượng: { {k: round(v,2) for k,v in eps.items()} }")

    bundle = {"forecaster": fc_full, "eps": eps,
              "trained_days": DAYS, "metrics": ev}
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(bundle, f)
    print(f"[train] ✅ Đã lưu model -> {MODEL_PATH}")
    print("[train] Giờ chạy API:  uvicorn ai_service.app:app --port 8100")


if __name__ == "__main__":
    main()
