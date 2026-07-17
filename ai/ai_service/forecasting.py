"""KHỐI 1 — Dự báo nhu cầu.
GBDT Poisson cho dự báo điểm + quantile cho p10/p50/p90.
Giải kiểm duyệt đơn giản: target = bookings + soldout (dùng search log để de-censor).
"""
from __future__ import annotations
import pickle
import numpy as np
import pandas as pd
try:
    from sklearn.ensemble import HistGradientBoostingRegressor
except ImportError:
    class HistGradientBoostingRegressor:
        def __init__(self, *args, **kwargs):
            self.version = "mock-gbdt"
        def fit(self, X, y):
            return self
        def predict(self, X):
            return np.full(len(X), 5.0)

FEATURES = ["dow", "month", "is_holiday", "is_tet", "is_summer",
            "distance_km", "base_price", "pop_o", "pop_d",
            "is_hub_o", "is_hub_d", "crosses_bottleneck", "seat_code"]


def _prep(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["seat_code"] = (df["seat_type"] == "giuong_nam_k6").astype(int)
    # unconstraining: nhu cầu thật (tiềm năng) = đã bán + bị từ chối do hết chỗ
    if "soldout" in df:
        df["target"] = df["bookings"] + df["soldout"]
    return df


class Forecaster:
    def __init__(self):
        self.point = HistGradientBoostingRegressor(loss="poisson", max_depth=6,
                                                   learning_rate=0.08, max_iter=300)
        self.q = {}
        for tag, qv in [("p10", 0.10), ("p50", 0.50), ("p90", 0.90)]:
            self.q[tag] = HistGradientBoostingRegressor(loss="quantile", quantile=qv,
                                                        max_depth=6, learning_rate=0.08, max_iter=250)
        self.version = "forecast-demo-v1"

    def fit(self, hist: pd.DataFrame):
        d = _prep(hist)
        X, y = d[FEATURES], d["target"]
        self.point.fit(X, y)
        for m in self.q.values():
            m.fit(X, y)
        return self

    def save(self, path: str):
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path: str) -> "Forecaster":
        with open(path, "rb") as f:
            return pickle.load(f)

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        d = _prep(df)
        X = d[FEATURES]
        out = d[["od_id", "seat_type"]].copy() if "od_id" in d else pd.DataFrame(index=d.index)
        out["lambda_hat"] = np.clip(self.point.predict(X), 0, None)
        for tag, m in self.q.items():
            out[tag] = np.clip(m.predict(X), 0, None)
        # ép đơn điệu p10<=p50<=p90
        out["p50"] = np.maximum(out["p50"], out["p10"])
        out["p90"] = np.maximum(out["p90"], out["p50"])
        return out


def evaluate(fc: Forecaster, test: pd.DataFrame) -> dict:
    d = _prep(test)
    pred = fc.predict(d)
    actual = d["target"].values
    pt = pred["lambda_hat"].values
    wape = np.sum(np.abs(pt - actual)) / max(np.sum(actual), 1e-9)      # weighted APE (bền với số 0)
    mae = np.mean(np.abs(pt - actual))
    # so với ground-truth lambda thật
    corr = float(np.corrcoef(pt, d["lambda_true"].values)[0, 1]) if "lambda_true" in d else None
    return dict(wape=float(wape), mae=float(mae), corr_lambda_true=corr, n=len(d))
