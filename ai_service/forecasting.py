"""KHỐI 1 — Dự báo nhu cầu.

• Mô hình điểm: Gradient Boosting hồi quy POISSON cho λ̂.
    - Ưu tiên LightGBM (objective='poisson'); tự fallback HistGradientBoosting (sklearn)
      nếu máy không có LightGBM. Interface không đổi.
• Phân vị p10/p50/p90: 3 mô hình quantile (pinball loss), ép đơn điệu p10≤p50≤p90.
• Nhãn (target): NHU CẦU ĐÃ GIẢI KIỂM DUYỆT bằng EM (unconstraining.py) — không phải số
  bán thô — nên mô hình không bị kéo tụt ở ngày cao điểm hết chỗ.
• Có: random-search tuning (time-split), feature importance (SHAP nếu có), pinball loss.
"""
from __future__ import annotations
import pickle
import numpy as np
import pandas as pd

from . import unconstraining

# LightGBM nếu có, không thì HistGradientBoosting
try:
    from lightgbm import LGBMRegressor
    _HAS_LGBM = True
except Exception:                                    # pragma: no cover
    _HAS_LGBM = False
from sklearn.ensemble import HistGradientBoostingRegressor

FEATURES = ["dow", "month", "is_holiday", "is_tet", "is_summer",
            "days_to_tet", "is_pre_tet", "is_post_tet", "is_rainy", "promo",
            "distance_km", "base_price", "pop_o", "pop_d",
            "is_hub_o", "is_hub_d", "crosses_bottleneck", "seat_code"]


def _ensure(df: pd.DataFrame) -> pd.DataFrame:
    """Bảo đảm mọi cột FEATURES tồn tại (điền 0 nếu người gọi chưa cấp) + seat_code."""
    d = df.copy()
    d["seat_code"] = (d["seat_type"] == "giuong_nam_k6").astype(int) if "seat_type" in d else 0
    for c in FEATURES:
        if c not in d.columns:
            d[c] = 0
    return d


def _make_target(hist: pd.DataFrame, use_em: bool) -> pd.Series:
    """Nhãn train = cầu đã giải kiểm duyệt (EM) nếu có soldout; fallback bookings(+soldout)."""
    if use_em and "soldout" in hist and "bookings" in hist:
        return unconstraining.unconstrain(hist)["demand_unconstrained"].astype(float)
    if "bookings" in hist:
        return (hist["bookings"] + hist.get("soldout", 0)).astype(float)
    raise ValueError("hist thiếu cột bookings để dựng target")


def _point_model(**kw):
    if _HAS_LGBM:
        base = dict(objective="poisson", n_estimators=400, learning_rate=0.05,
                    num_leaves=31, min_child_samples=40, subsample=0.9,
                    colsample_bytree=0.9, verbosity=-1)
        base.update(kw)
        return LGBMRegressor(**base)
    return HistGradientBoostingRegressor(loss="poisson", max_depth=6,
                                         learning_rate=0.08, max_iter=300)


def _quantile_model(q, **kw):
    if _HAS_LGBM:
        base = dict(objective="quantile", alpha=q, n_estimators=300, learning_rate=0.05,
                    num_leaves=31, min_child_samples=40, verbosity=-1)
        base.update(kw)
        return LGBMRegressor(**base)
    return HistGradientBoostingRegressor(loss="quantile", quantile=q, max_depth=6,
                                         learning_rate=0.08, max_iter=250)


def pinball_loss(y, q_pred, alpha) -> float:
    y = np.asarray(y, float); q_pred = np.asarray(q_pred, float)
    e = y - q_pred
    return float(np.mean(np.maximum(alpha * e, (alpha - 1) * e)))


class Forecaster:
    def __init__(self):
        self.point = None
        self.q = {}
        self.best_params = {}
        self.backend = "lightgbm" if _HAS_LGBM else "histgb"
        self.version = "forecast-v2"

    # ---------- tuning ----------
    def _tune(self, X, y, dates, n_trials=8, seed=0):
        """Random-search cho model điểm, đánh giá trên VALID theo thời gian (20% ngày cuối)."""
        if not _HAS_LGBM:
            return {}
        rng = np.random.default_rng(seed)
        udates = np.sort(pd.unique(dates))
        cut = udates[int(len(udates) * 0.8)]
        tr, va = dates < cut, dates >= cut
        if va.sum() < 50 or tr.sum() < 50:
            return {}
        grid = dict(num_leaves=[15, 31, 63, 95],
                    learning_rate=[0.03, 0.05, 0.08],
                    n_estimators=[300, 500, 800],
                    min_child_samples=[20, 40, 80])
        best, best_score = {}, np.inf
        for _ in range(n_trials):
            cand = {k: rng.choice(v).item() for k, v in grid.items()}
            m = _point_model(**cand)
            m.fit(X[tr], y[tr])
            pred = np.clip(m.predict(X[va]), 1e-6, None)
            # Poisson deviance (thấp = tốt)
            yv = np.clip(y[va], 1e-9, None)
            dev = float(np.mean(2 * (yv * np.log(yv / pred) - (yv - pred))))
            if dev < best_score:
                best_score, best = dev, cand
        return best

    # ---------- fit ----------
    def fit(self, hist: pd.DataFrame, use_em: bool = True, tune: bool = False):
        d = _ensure(hist)
        X = d[FEATURES].values
        y = _make_target(hist, use_em).values
        if tune and "service_date" in hist:
            self.best_params = self._tune(X, y, pd.to_datetime(hist["service_date"]).values)
        self.point = _point_model(**self.best_params)
        self.point.fit(X, y)
        for tag, qv in [("p10", 0.10), ("p50", 0.50), ("p90", 0.90)]:
            m = _quantile_model(qv, **{k: v for k, v in self.best_params.items()
                                       if k in ("num_leaves", "learning_rate", "min_child_samples")})
            m.fit(X, y)
            self.q[tag] = m
        return self

    # ---------- predict ----------
    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        d = _ensure(df)
        X = d[FEATURES].values
        out = d[["od_id", "seat_type"]].copy() if "od_id" in d else pd.DataFrame(index=d.index)
        out["lambda_hat"] = np.clip(self.point.predict(X), 0, None)
        for tag, m in self.q.items():
            out[tag] = np.clip(m.predict(X), 0, None)
        out["p50"] = np.maximum(out["p50"], out["p10"])       # ép đơn điệu
        out["p90"] = np.maximum(out["p90"], out["p50"])
        return out

    # ---------- feature importance ----------
    def feature_importance(self, X_sample: pd.DataFrame | None = None, n=2000) -> pd.DataFrame:
        """Trả DataFrame [feature, importance] — SHAP nếu có, không thì gain/impurity."""
        try:
            import shap
            if X_sample is None:
                raise ValueError("cần X_sample cho SHAP")
            Xs = _ensure(X_sample)[FEATURES]
            Xs = Xs.sample(min(n, len(Xs)), random_state=0) if len(Xs) > n else Xs
            expl = shap.TreeExplainer(self.point)
            sv = expl.shap_values(Xs)
            imp = np.abs(sv).mean(axis=0)
            method = "shap"
        except Exception:
            if hasattr(self.point, "feature_importances_"):
                imp = np.asarray(self.point.feature_importances_, float)
                method = "gain"
            else:                                              # HistGB: permutation nhẹ
                imp = np.ones(len(FEATURES)); method = "n/a"
        s = pd.DataFrame({"feature": FEATURES, "importance": imp, "method": method})
        return s.sort_values("importance", ascending=False).reset_index(drop=True)

    # ---------- lưu/nạp ----------
    def save(self, path):
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path) -> "Forecaster":
        with open(path, "rb") as f:
            return pickle.load(f)


def evaluate(fc: Forecaster, test: pd.DataFrame, use_em: bool = True) -> dict:
    d = _ensure(test)
    y = _make_target(test, use_em).values
    pred = fc.predict(test)
    pt = pred["lambda_hat"].values
    wape = np.sum(np.abs(pt - y)) / max(np.sum(y), 1e-9)
    mae = float(np.mean(np.abs(pt - y)))
    corr = float(np.corrcoef(pt, d["lambda_true"].values)[0, 1]) if "lambda_true" in d else None
    pinball = {tag: pinball_loss(y, pred[tag].values, a)
               for tag, a in [("p10", 0.10), ("p50", 0.50), ("p90", 0.90)]}
    cov80 = float(((y >= pred["p10"].values) & (y <= pred["p90"].values)).mean())
    return dict(wape=float(wape), mae=mae, corr_lambda_true=corr,
                pinball=pinball, coverage_80=cov80, n=len(d), backend=fc.backend)
