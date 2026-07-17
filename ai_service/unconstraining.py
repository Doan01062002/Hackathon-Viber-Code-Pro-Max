"""Giải kiểm duyệt nhu cầu bằng EM (Expectation-Maximization) — censored Poisson.

VẤN ĐỀ: khi một sản phẩm HẾT CHỖ, số vé bán được là bản KIỂM DUYỆT của nhu cầu thật
(true demand ≥ số quan sát). Nếu train thẳng trên số bán, mô hình học tụt so với nhu cầu
thật ở đúng những ngày cao điểm -> dự báo thấp -> tối ưu/định giá sai.

Ý tưởng EM (Salch 1997, cổ điển trong revenue management):
  Giả định nhu cầu D ~ Poisson(λ_nhóm). Với bản ghi KHÔNG kiểm duyệt, D = quan sát.
  Với bản ghi BỊ kiểm duyệt tại mức k (đã bán hết k chỗ), ta chỉ biết D ≥ k.
    • E-step: thay D bằng kỳ vọng có điều kiện  E[D | D ≥ k, λ].
    • M-step: cập nhật λ = trung bình các D (đã impute) trong nhóm.
  Lặp tới hội tụ. Nhóm = (OD vật lý × trạng thái mùa) để λ trong nhóm xấp xỉ hằng.

Công thức Poisson:  E[X · 1{X ≥ k}] = λ · P(X ≥ k-1)  ⇒  E[X | X ≥ k] = λ · P(X≥k-1)/P(X≥k).

API:
  unconstrain(hist) -> hist + cột 'demand_unconstrained' (nhãn dùng để train Khối 1).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import poisson


def _cond_expectation(lam: float, k: int) -> float:
    """E[X | X ≥ k] với X ~ Poisson(lam). k = mức bị kiểm duyệt (đã biết D ≥ k)."""
    if k <= 0:
        return lam
    sf_k = poisson.sf(k - 1, lam)        # P(X ≥ k)
    sf_km1 = poisson.sf(k - 2, lam)      # P(X ≥ k-1)
    if sf_k <= 1e-12:                    # đuôi quá mỏng -> λ nhỏ hơn k nhiều: nhu cầu ~ k
        return float(k)
    return float(lam * sf_km1 / sf_k)


def _em_group(obs: np.ndarray, censored: np.ndarray, max_iter=100, tol=1e-6):
    """EM cho một nhóm. obs = số quan sát (điểm kiểm duyệt), censored = cờ bị cắt.
    Trả (lam_hội_tụ, demand_impute mỗi bản ghi)."""
    obs = obs.astype(float)
    lam = max(obs.mean(), 0.1)           # khởi tạo bằng trung bình quan sát
    for _ in range(max_iter):
        d = obs.copy()
        idx = np.where(censored)[0]
        for i in idx:                    # E-step: impute bản ghi bị cắt
            d[i] = _cond_expectation(lam, int(round(obs[i])))
        new_lam = max(d.mean(), 1e-6)    # M-step
        if abs(new_lam - lam) < tol:
            lam = new_lam
            break
        lam = new_lam
    # impute cuối theo lam hội tụ
    d = obs.copy()
    for i in np.where(censored)[0]:
        d[i] = _cond_expectation(lam, int(round(obs[i])))
    return lam, d


def unconstrain(hist: pd.DataFrame,
                observed_col: str | None = None,
                group_cols=("od_id", "is_tet", "is_holiday")) -> pd.DataFrame:
    """Thêm cột 'demand_unconstrained' = nhu cầu thật ước lượng (đã de-censor bằng EM).

    observed_col: cột quan sát làm mốc kiểm duyệt. Mặc định = bookings + soldout nếu có
      (ta đã biết cầu ≥ số này), fallback = bookings.
    Bản ghi coi là BỊ kiểm duyệt khi soldout > 0 (có người bị từ chối vì hết chỗ).
    """
    h = hist.copy()
    if observed_col is None:
        if "soldout" in h:
            h["_obs"] = (h["bookings"] + h["soldout"]).astype(float)
        else:
            h["_obs"] = h["bookings"].astype(float)
        observed_col = "_obs"
    h["_censored"] = (h["soldout"] > 0) if "soldout" in h else False

    gcols = [c for c in group_cols if c in h.columns]
    h["demand_unconstrained"] = h[observed_col].astype(float)
    lam_map = {}
    for key, g in h.groupby(gcols):
        lam, d = _em_group(g[observed_col].values, g["_censored"].values.astype(bool))
        h.loc[g.index, "demand_unconstrained"] = d
        lam_map[key if isinstance(key, tuple) else (key,)] = lam
    # không bao giờ nhỏ hơn mốc đã biết (cầu ≥ bookings+soldout)
    h["demand_unconstrained"] = np.maximum(h["demand_unconstrained"], h[observed_col])
    h.drop(columns=["_obs", "_censored"], errors="ignore", inplace=True)
    return h


def uplift_report(hist: pd.DataFrame) -> dict:
    """Thống kê mức 'kéo lên' của EM so với số bán thô — để minh chứng tác dụng."""
    h = unconstrain(hist)
    obs = (h["bookings"] + h.get("soldout", 0)).sum()
    unc = h["demand_unconstrained"].sum()
    cens = int((h.get("soldout", pd.Series([0])) > 0).sum())
    return dict(observed_sum=float(obs), unconstrained_sum=float(unc),
                uplift_pct=float((unc - obs) / max(obs, 1) * 100), censored_rows=cens)
