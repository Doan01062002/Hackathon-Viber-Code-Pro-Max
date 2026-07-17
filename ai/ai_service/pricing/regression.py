"""AI-15.2 — Hồi quy OLS/2SLS thuần (numpy) + biến công cụ Hausman.

Máy móc thống kê dùng chung cho ước lượng ε/α (elasticity.py) — không chứa logic
nghiệp vụ pricing, chỉ là công cụ hồi quy tuyến tính/2SLS thuần túy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class OLSResult:
    """Kết quả hồi quy OLS tối giản — đủ để kiểm định (se, t-stat, p-value, R²)."""

    beta: np.ndarray
    se: np.ndarray
    t_stats: np.ndarray
    r2: float
    n: int
    dof: int

    @property
    def p_values(self) -> np.ndarray:
        return 2 * stats.t.sf(np.abs(self.t_stats), self.dof)


def _ols_with_stats(X: np.ndarray, y: np.ndarray) -> OLSResult:
    """Hồi quy OLS bằng đại số tuyến tính thuần (không thêm dependency statsmodels
    chỉ cho vài hồi quy nhỏ). X phải đã có cột hằng số (intercept) ở vị trí đầu."""
    n, k = X.shape
    beta, _residuals, _rank, _sv = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    dof = max(n - k, 1)
    sigma2 = float(resid @ resid) / dof
    xtx_inv = np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.clip(np.diag(sigma2 * xtx_inv), 0, None))
    t_stats = np.divide(beta, se, out=np.full_like(beta, np.nan), where=se > 0)
    ss_res = float(resid @ resid)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return OLSResult(beta=beta, se=se, t_stats=t_stats, r2=r2, n=n, dof=dof)


def _leave_one_out_instrument(df: pd.DataFrame, group_cols: list[str], value_col: str) -> np.ndarray:
    """Biến công cụ Hausman: giá trung bình cùng nhóm (vd cùng OD), LOẠI TRỪ chính
    quan sát đang xét, dùng làm biến công cụ cho giá của quan sát đó.

    Vì đây là trung bình trên nhiều ngày khác, nó phản ánh mức giá hệ thống của
    nhóm (base_price, chính sách markup trung bình) chứ không phải sốc cầu riêng của
    đúng ngày đang xét — thỏa điều kiện liên quan (correlated với giá) và độc lập
    tương đối với nhiễu ngày đó (miễn các sốc cầu theo ngày không tự tương quan mạnh),
    nên xử lý được vấn đề nội sinh (giá phản ứng ngược lại theo cầu quan sát được).
    """
    grp = df.groupby(group_cols)[value_col]
    count = grp.transform("count")
    total = grp.transform("sum")
    denom = (count - 1).clip(lower=1)
    return ((total - df[value_col]) / denom).to_numpy(dtype=float)


def _two_stage_least_squares(
    endogenous: np.ndarray, instrument: np.ndarray, controls: np.ndarray, y: np.ndarray
) -> tuple[OLSResult, OLSResult]:
    """2SLS thủ công:
    Stage 1 — hồi quy biến nội sinh (giá hoặc log giá) theo biến công cụ + control,
    lấy giá trị DỰ ĐOÁN (phần biến thiên "ngoại sinh" của giá, đã lọc bỏ phần tương
    quan với nhiễu hồi quy ở Stage 2).
    Stage 2 — hồi quy y theo giá trị dự đoán đó + control. Hệ số thu được không còn bị
    thiên lệch do nội sinh, miễn biến công cụ thỏa exclusion restriction.
    """
    n = len(y)
    ones = np.ones((n, 1))
    instrument = instrument.reshape(-1, 1)
    X1 = np.hstack([ones, instrument, controls]) if controls.size else np.hstack([ones, instrument])
    stage1 = _ols_with_stats(X1, endogenous)
    fitted = X1 @ stage1.beta

    fitted = fitted.reshape(-1, 1)
    X2 = np.hstack([ones, fitted, controls]) if controls.size else np.hstack([ones, fitted])
    stage2 = _ols_with_stats(X2, y)
    return stage1, stage2
