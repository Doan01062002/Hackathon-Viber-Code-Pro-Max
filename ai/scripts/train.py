"""HUẤN LUYỆN MỘT LẦN (MVP) — train Khối 1 + booking curve + co giãn rồi LƯU ra file.
App nạp file này thay vì train lúc khởi động.

Bao gồm:
  • Giải kiểm duyệt EM (unconstraining) làm nhãn train  [tự động trong Forecaster.fit]
  • LightGBM Poisson + tuning (random-search theo time-split) nếu bật --tune
  • Quantile p10/p50/p90 + pinball loss trên backtest
  • Fit booking curve (từ lead_time nếu train trên seeds; không thì đường lý thuyết)
  • Ước lượng độ co giãn (Khối 3)

Chạy:  python scripts/train.py --from-seeds out/seeds --tune
       python scripts/train.py                       # tự sinh bằng datagen
"""
from __future__ import annotations
import sys, os, pickle, warnings, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
warnings.filterwarnings("ignore")
from datetime import date
import pandas as pd
from ai_service import datagen, forecasting, pricing, booking_curve as BC

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(REPO, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "model1.pkl")
START, DAYS = date(2023, 1, 1), 730


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-seeds", type=str, default=None,
                    help="thư mục 21 bảng CSV (vd out/seeds). Bỏ trống = tự sinh bằng datagen.")
    ap.add_argument("--tune", action="store_true", help="bật random-search tuning cho LightGBM")
    args = ap.parse_args()
    os.makedirs(MODEL_DIR, exist_ok=True)

    if args.from_seeds:
        from ai_service import adapter
        print(f"[train] Nạp dữ liệu THẬT từ 21 bảng: {args.from_seeds} ...")
        hist = adapter.load_history(args.from_seeds)
    else:
        print(f"[train] Tự sinh dữ liệu bằng datagen ({DAYS} ngày) ...")
        hist = datagen.simulate(START, DAYS, seed=7)["history"].copy()
    hist["service_date"] = pd.to_datetime(hist["service_date"])

    # giải kiểm duyệt: minh chứng mức 'kéo lên' của EM
    from ai_service import unconstraining
    up = unconstraining.uplift_report(hist)
    print(f"[train] EM giải kiểm duyệt: quan sát {up['observed_sum']:.0f} -> "
          f"nhu cầu thật {up['unconstrained_sum']:.0f}  (+{up['uplift_pct']:.1f}%, "
          f"{up['censored_rows']} bản ghi bị cắt)")

    # tách train/test theo thời gian (80/20)
    dts = sorted(hist["service_date"].unique())
    split = dts[int(len(dts) * 0.8)]
    train = hist[hist.service_date < split]
    test = hist[hist.service_date >= split]

    print(f"[train] Huấn luyện Forecaster (train {len(train):,} / test {len(test):,}"
          f"{' , tuning ON' if args.tune else ''}) ...")
    fc = forecasting.Forecaster().fit(train, use_em=True, tune=args.tune)
    ev = forecasting.evaluate(fc, test)
    corr = ev.get("corr_lambda_true")
    corr_s = f"{corr:.3f}" if corr is not None else "n/a (data thật không có ground-truth)"
    pb = ev["pinball"]
    print(f"[train] Backtest [{ev['backend']}]: WAPE={ev['wape']*100:.1f}%  corr(λ̂,λ_thật)={corr_s}  "
          f"phủ p10–p90={ev['coverage_80']*100:.0f}%  "
          f"pinball(p10/p50/p90)={pb['p10']:.2f}/{pb['p50']:.2f}/{pb['p90']:.2f}")
    if args.tune and fc.best_params:
        print(f"[train] Tham số tốt nhất: {fc.best_params}")

    # feature importance (SHAP nếu có)
    try:
        fi = fc.feature_importance(train).head(6)
        print("[train] Top đặc trưng (" + fi["method"].iloc[0] + "): " +
              ", ".join(f"{r.feature}={r.importance:.2f}" for r in fi.itertuples()))
    except Exception as e:
        print(f"[train] (bỏ qua feature importance: {e})")

    # train lại trên TOÀN BỘ để phục vụ (giữ tham số đã tune)
    fc_full = forecasting.Forecaster()
    fc_full.best_params = fc.best_params
    fc_full.fit(hist, use_em=True, tune=False)

    # booking curve
    if args.from_seeds:
        try:
            lt = adapter.load_bookings_leadtime(args.from_seeds)
            bc = BC.fit(lt, horizon=60)
            evb = BC.evaluate(bc, lt, at_days=14)
            mape = evb["pickup_mape"]
            print(f"[train] Booking curve (lead_time thật): pickup MAPE@14 ngày="
                  f"{mape:.1f}% ({evb['n_trips']} chuyến)" if mape is not None
                  else "[train] Booking curve fit (không đủ chuyến để đo MAPE)")
        except Exception as e:
            print(f"[train] (không đọc được lead_time từ seeds: {e}) -> đường lý thuyết")
            bc = BC.fit_theoretical(60, 15.0)
    else:
        bc = BC.fit_theoretical(60, 15.0)
        print("[train] Booking curve: đường lý thuyết exp(-lead/15) (datagen không xuất lead_time)")

    eps = pricing.estimate_elasticity(hist)
    print(f"[train] Độ co giãn ước lượng: { {k: round(v,2) for k,v in eps.items()} }")

    bundle = {"forecaster": fc_full, "eps": eps, "booking_curve": bc.to_dict(),
              "trained_days": len(dts), "metrics": ev}
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(bundle, f)
    print(f"[train] ✅ Đã lưu model -> {MODEL_PATH}")
    print("[train] Backend sẽ tự nạp model này khi khởi động:  uvicorn backend.main:app --port 8000")


if __name__ == "__main__":
    main()
