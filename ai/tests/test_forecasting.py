"""Test Khối 1 — Forecaster (ai_service/forecasting.py): giải kiểm duyệt (_prep), fit/
predict (điểm + quantile), ép đơn điệu quantile, save/load, evaluate()."""

from datetime import date

import numpy as np
import pandas as pd
from ai_service import datagen
from ai_service import forecasting as F


def _synthetic_history(n: int = 400, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    seat_type = rng.choice(["ngoi_mem", "giuong_nam_k6"], n)
    distance_km = rng.uniform(50, 1700, n)
    bookings = rng.poisson(5, n)
    soldout = rng.integers(0, 3, n)
    return pd.DataFrame(
        dict(
            od_id=np.arange(n),
            seat_type=seat_type,
            dow=rng.integers(0, 7, n),
            month=rng.integers(1, 13, n),
            is_holiday=rng.integers(0, 2, n),
            is_tet=np.zeros(n, dtype=int),
            is_summer=rng.integers(0, 2, n),
            distance_km=distance_km,
            base_price=20_000 + distance_km * 700,
            pop_o=rng.uniform(0.2, 1.0, n),
            pop_d=rng.uniform(0.2, 1.0, n),
            is_hub_o=rng.integers(0, 2, n),
            is_hub_d=rng.integers(0, 2, n),
            crosses_bottleneck=rng.integers(0, 2, n),
            bookings=bookings,
            soldout=soldout,
            lambda_true=bookings + soldout + rng.normal(0, 0.1, n),
        )
    )


# ============================================================
# _prep — giải kiểm duyệt (unconstraining) + đặc trưng seat_code
# ============================================================


def test_prep_computes_seat_code_from_seat_type():
    df = pd.DataFrame(dict(seat_type=["ngoi_mem", "giuong_nam_k6"], bookings=[1, 2], soldout=[0, 1]))
    out = F._prep(df)
    assert list(out["seat_code"]) == [0, 1]


def test_prep_unconstrains_target_as_bookings_plus_soldout():
    df = pd.DataFrame(dict(seat_type=["ngoi_mem"], bookings=[5], soldout=[3]))
    out = F._prep(df)
    assert out["target"].iloc[0] == 8


def test_prep_no_target_column_when_soldout_missing():
    # lúc predict (không train), df không có bookings/soldout -> không có target,
    # _prep không được raise lỗi vì thiếu cột đó.
    df = pd.DataFrame(dict(seat_type=["ngoi_mem"]))
    out = F._prep(df)
    assert "target" not in out.columns


def test_prep_does_not_mutate_input_dataframe():
    df = pd.DataFrame(dict(seat_type=["ngoi_mem"], bookings=[5], soldout=[3]))
    F._prep(df)
    assert "seat_code" not in df.columns
    assert "target" not in df.columns


# ============================================================
# fit / predict
# ============================================================


def test_fit_predict_returns_expected_columns_and_nonnegative():
    hist = _synthetic_history()
    fc = F.Forecaster().fit(hist)
    pred = fc.predict(hist)

    assert {"od_id", "seat_type", "lambda_hat", "p10", "p50", "p90"}.issubset(pred.columns)
    assert len(pred) == len(hist)
    assert (pred["lambda_hat"] >= 0).all()
    assert (pred[["p10", "p50", "p90"]] >= 0).all().all()


def test_predict_enforces_monotonic_quantiles_on_real_model():
    hist = _synthetic_history()
    fc = F.Forecaster().fit(hist)
    pred = fc.predict(hist)

    assert (pred["p10"] <= pred["p50"] + 1e-9).all()
    assert (pred["p50"] <= pred["p90"] + 1e-9).all()


def test_predict_forces_monotonic_even_when_underlying_quantile_models_cross():
    """Kiểm tra riêng bước ép đơn điệu (predict() dòng p50=max(p50,p10), p90=max(p90,
    p50)) độc lập với việc mô hình quantile bên dưới có tự nhiên đơn điệu hay không —
    giả lập 3 mô hình trả về p10=50 > p50=10 > p90=5 (nghịch đảo hoàn toàn)."""
    hist = _synthetic_history(n=20)
    fc = F.Forecaster().fit(hist)
    fc.q["p10"].predict = lambda X: np.full(len(X), 50.0)
    fc.q["p50"].predict = lambda X: np.full(len(X), 10.0)
    fc.q["p90"].predict = lambda X: np.full(len(X), 5.0)

    pred = fc.predict(hist)

    assert (pred["p10"] == 50.0).all()
    assert (pred["p50"] == 50.0).all()  # bị kéo lên bằng p10 vì max(10,50)
    assert (pred["p90"] == 50.0).all()  # bị kéo lên tiếp vì max(5,50)
    assert (pred["p10"] <= pred["p50"]).all()
    assert (pred["p50"] <= pred["p90"]).all()


def test_predict_clips_negative_model_output_to_zero():
    hist = _synthetic_history(n=20)
    fc = F.Forecaster().fit(hist)
    fc.point.predict = lambda X: np.full(len(X), -3.0)
    pred = fc.predict(hist)
    assert (pred["lambda_hat"] == 0.0).all()


def test_predict_without_od_id_column_still_works():
    hist = _synthetic_history()
    fc = F.Forecaster().fit(hist)
    df_no_id = hist.drop(columns=["od_id"])

    pred = fc.predict(df_no_id)

    assert "od_id" not in pred.columns
    assert len(pred) == len(df_no_id)


# ============================================================
# save / load
# ============================================================


def test_save_load_roundtrip_preserves_predictions(tmp_path):
    hist = _synthetic_history()
    fc = F.Forecaster().fit(hist)
    path = tmp_path / "model.pkl"

    fc.save(str(path))
    loaded = F.Forecaster.load(str(path))

    pred_original = fc.predict(hist)
    pred_loaded = loaded.predict(hist)
    pd.testing.assert_frame_equal(pred_original, pred_loaded)
    assert loaded.version == fc.version


# ============================================================
# evaluate()
# ============================================================


def test_evaluate_returns_expected_keys_and_valid_ranges():
    hist = _synthetic_history()
    train, test = hist.iloc[:300].copy(), hist.iloc[300:].copy()
    fc = F.Forecaster().fit(train)

    metrics = F.evaluate(fc, test)

    assert set(metrics.keys()) == {"wape", "mae", "corr_lambda_true", "n"}
    assert metrics["n"] == len(test)
    assert metrics["wape"] >= 0
    assert metrics["mae"] >= 0
    assert metrics["corr_lambda_true"] is not None
    assert -1.0 <= metrics["corr_lambda_true"] <= 1.0


def test_evaluate_corr_is_none_without_lambda_true_column():
    hist = _synthetic_history().drop(columns=["lambda_true"])
    fc = F.Forecaster().fit(hist)

    metrics = F.evaluate(fc, hist)

    assert metrics["corr_lambda_true"] is None


def test_evaluate_wape_handles_all_zero_actual_without_zero_division():
    # Model train trên dữ liệu bình thường (loss="poisson" của sklearn đòi hỏi
    # sum(y) > 0 nên KHÔNG thể train trên toàn bộ target=0 — đó là giới hạn hợp lý của
    # bài toán, không phải case cần xử lý). Case thực tế cần an toàn là: TẬP TEST/ĐÁNH
    # GIÁ tình cờ toàn cầu 0 (ví dụ OD/ngày rất vắng khách) trong khi model đã train ổn.
    hist = _synthetic_history(n=50)
    fc = F.Forecaster().fit(hist)

    zero_actual_test = hist.copy()
    zero_actual_test["bookings"] = 0
    zero_actual_test["soldout"] = 0

    metrics = F.evaluate(fc, zero_actual_test)

    assert np.isfinite(metrics["wape"])
    assert np.isfinite(metrics["mae"])


# ============================================================
# Tích hợp với dữ liệu mô phỏng thật (datagen) — như scripts/train.py
# ============================================================


def test_forecaster_end_to_end_on_real_datagen_history():
    sim = datagen.simulate(start=date(2024, 1, 1), days=40)
    hist = sim["history"]

    fc = F.Forecaster().fit(hist)
    pred = fc.predict(hist.head(50))

    assert len(pred) == 50
    assert (pred["p10"] <= pred["p50"] + 1e-9).all()
    assert (pred["p50"] <= pred["p90"] + 1e-9).all()
    assert (pred["lambda_hat"] >= 0).all()
