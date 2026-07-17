"""Test Khối 3 — ước lượng co giãn (2SLS + biến công cụ) và pricing markup + diễn giải
(ai_service/pricing.py)."""

import numpy as np
import pandas as pd
import pytest
from ai_service import config as C
from ai_service import pricing

REQUIRED_COLS = dict(
    dow=0,
    month=1,
    is_holiday=0,
    is_tet=0,
    distance_km=100.0,
)


def _history_row(**overrides):
    row = dict(od_id=0, seat_type="ngoi_mem", shown_price=100.0, willing=5, **REQUIRED_COLS)
    row.update(overrides)
    return row


def _od(seat_type="ngoi_mem", segments=(0,), base_price=100_000, od_id=1):
    return dict(od_id=od_id, seat_type=seat_type, segments=list(segments), base_price=base_price)


def _endogenous_price_demand_panel(n_groups=40, days=150, true_eps=2.2, seed=123) -> pd.DataFrame:
    """DGP tổng hợp có NỘI SINH thật: giá phản ứng theo sốc cầu chung của ngày đó
    (price = base_p * exp(0.5*shock + nhiễu)), và cầu cũng chịu tác động trực tiếp bởi
    cùng sốc đó (qty = base_q * exp(shock) * (price/100)^-eps) — mô phỏng tình huống
    người bán tăng giá khi thấy dấu hiệu cầu tăng (dynamic pricing), khiến hồi quy OLS
    thường bị lệch. `base_p` (mức giá hệ thống theo OD) không đổi theo ngày nên biến
    công cụ leave-one-out (chủ yếu phản ánh base_p) độc lập tương đối với sốc riêng
    từng ngày -> dùng được để nhận diện ε thật.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for g in range(n_groups):
        base_p = rng.uniform(50, 150)
        base_q = rng.uniform(80, 200)
        for t in range(days):
            shock = rng.normal(0, 0.3)
            price = base_p * np.exp(0.5 * shock + rng.normal(0, 0.05))
            qty_mean = base_q * np.exp(shock) * (price / 100.0) ** (-true_eps)
            qty = rng.poisson(max(qty_mean, 0.1))
            rows.append(
                dict(
                    od_id=g,
                    seat_type="ngoi_mem",
                    shown_price=price,
                    willing=int(qty),
                    dow=t % 7,
                    month=1,
                    is_holiday=0,
                    is_tet=0,
                    distance_km=100.0,
                )
            )
    df = pd.DataFrame(rows)
    return df[df["willing"] > 0].reset_index(drop=True)


def _naive_ols_log_log_elasticity(df: pd.DataFrame) -> float:
    """OLS log-log KHÔNG có biến công cụ — dùng làm baseline để so sánh độ lệch."""
    lp = np.log(df["shown_price"].to_numpy())
    lq = np.log(df["willing"].to_numpy())
    X = np.column_stack([np.ones(len(lp)), lp])
    beta, *_ = np.linalg.lstsq(X, lq, rcond=None)
    return -beta[1]


# ============================================================
# AI-09 — Chuẩn bị dữ liệu giá–lượng
# ============================================================


def test_prepare_price_quantity_data_raises_on_missing_columns():
    df = pd.DataFrame({"od_id": [1], "seat_type": ["ngoi_mem"]})
    with pytest.raises(ValueError, match="thiếu cột"):
        pricing.prepare_price_quantity_data(df)


def test_prepare_price_quantity_data_filters_invalid_rows():
    df = pd.DataFrame(
        [
            _history_row(shown_price=100.0, willing=5),
            _history_row(shown_price=0.0, willing=5),  # giá <=0 -> loại
            _history_row(shown_price=100.0, willing=np.nan),  # thiếu lượng -> loại
        ]
    )
    out = pricing.prepare_price_quantity_data(df)
    assert len(out) == 1
    assert set(pricing.PRICE_QTY_COLUMNS).issubset(out.columns)


# ============================================================
# AI-15.2 — OLS/2SLS thuần + biến công cụ Hausman
# ============================================================


def test_ols_with_stats_recovers_known_coefficients_noiseless():
    rng = np.random.default_rng(0)
    n = 200
    x = rng.uniform(0, 10, n)
    y = 3.0 + 2.5 * x  # không nhiễu -> khớp tuyệt đối
    X = np.column_stack([np.ones(n), x])
    res = pricing._ols_with_stats(X, y)
    assert res.beta[0] == pytest.approx(3.0, abs=1e-8)
    assert res.beta[1] == pytest.approx(2.5, abs=1e-8)
    assert res.r2 == pytest.approx(1.0, abs=1e-6)


def test_ols_with_stats_p_values_in_valid_range():
    rng = np.random.default_rng(1)
    n = 100
    x = rng.normal(size=n)
    y = 1.0 + 0.5 * x + rng.normal(scale=0.1, size=n)
    X = np.column_stack([np.ones(n), x])
    res = pricing._ols_with_stats(X, y)
    assert np.all(res.p_values >= 0.0) and np.all(res.p_values <= 1.0)
    assert res.p_values[1] < 0.05  # hệ số thật khác 0 rõ ràng


def test_leave_one_out_instrument_excludes_current_row():
    df = pd.DataFrame({"od_id": [1, 1, 1], "shown_price": [10.0, 20.0, 30.0]})
    inst = pricing._leave_one_out_instrument(df, ["od_id"], "shown_price")
    np.testing.assert_allclose(inst, [25.0, 20.0, 15.0])  # (20+30)/2, (10+30)/2, (10+20)/2


def test_leave_one_out_instrument_separates_groups():
    df = pd.DataFrame({"od_id": [1, 1, 2, 2], "shown_price": [10.0, 20.0, 100.0, 200.0]})
    inst = pricing._leave_one_out_instrument(df, ["od_id"], "shown_price")
    np.testing.assert_allclose(inst, [20.0, 10.0, 200.0, 100.0])


# ============================================================
# 2SLS xử lý nội sinh — kiểm chứng thực nghiệm so với OLS thường
# ============================================================


def test_2sls_recovers_true_elasticity_close_than_naive_ols_under_endogeneity():
    df = _endogenous_price_demand_panel(true_eps=2.2)
    ols_eps = _naive_ols_log_log_elasticity(df)

    est = pricing._estimate_2sls(
        df.assign(log_price=np.log(df["shown_price"])),
        endogenous_col="log_price",
        fallback=1.5,
        min_obs=300,
        sign=-1.0,
    )

    assert not est.used_fallback
    assert abs(est.value - 2.2) < abs(ols_eps - 2.2)  # 2SLS gần giá trị thật hơn OLS
    assert abs(est.value - 2.2) < 0.15  # sát giá trị thật (2.2)
    assert abs(ols_eps - 2.2) > 0.2  # OLS thực sự lệch đáng kể (minh chứng nội sinh)
    assert est.first_stage_r2 > 0.3  # biến công cụ đủ mạnh, không phải weak instrument


def test_2sls_falls_back_when_insufficient_data():
    df = pd.DataFrame([_history_row()])  # 1 dòng, quá ít
    est = pricing._estimate_2sls(
        df.assign(log_price=np.log(df["shown_price"])),
        endogenous_col="log_price",
        fallback=1.7,
        min_obs=300,
        sign=-1.0,
    )
    assert est.used_fallback is True
    assert est.value == 1.7
    assert est.reason == "insufficient_data"


# ============================================================
# AI-15.4 — Kiểm định ước lượng
# ============================================================


def test_validate_elasticity_estimate_rejects_insignificant_t_stat():
    est = pricing.ElasticityEstimate(value=2.0, t_stat=1.0, first_stage_r2=0.5)
    assert pricing.validate_elasticity_estimate(est) is False


def test_validate_elasticity_estimate_rejects_weak_instrument():
    est = pricing.ElasticityEstimate(value=2.0, t_stat=5.0, first_stage_r2=0.0001)
    assert pricing.validate_elasticity_estimate(est) is False


def test_validate_elasticity_estimate_rejects_value_below_one():
    est = pricing.ElasticityEstimate(value=0.8, t_stat=5.0, first_stage_r2=0.5)
    assert pricing.validate_elasticity_estimate(est) is False


def test_validate_elasticity_estimate_accepts_valid_estimate():
    est = pricing.ElasticityEstimate(value=2.0, t_stat=5.0, first_stage_r2=0.5)
    assert pricing.validate_elasticity_estimate(est) is True


# ============================================================
# AI-15.1 + AI-15.3 — estimate_elasticity_iv / estimate_exponential_alpha_iv theo phân khúc
# ============================================================


def test_estimate_elasticity_iv_uses_only_matching_seat_type():
    df = _endogenous_price_demand_panel(true_eps=2.2)
    df["seat_type"] = "ngoi_mem"
    other = _endogenous_price_demand_panel(true_eps=2.2, seed=999)
    other["seat_type"] = "giuong_nam_k6"
    other["od_id"] += 1000  # tránh trùng od_id giữa 2 phân khúc
    combined = pd.concat([df, other], ignore_index=True)

    est = pricing.estimate_elasticity_iv(combined, "ngoi_mem", min_obs=300)
    assert not est.used_fallback
    assert est.value == pytest.approx(2.2, abs=0.2)


def test_estimate_elasticity_iv_clips_to_bounds():
    # ε thật cực lớn (8.0) vượt ELASTICITY_CAP -> phải bị clip, không trả thẳng 8.0
    df = _endogenous_price_demand_panel(true_eps=8.0)
    df["seat_type"] = "ngoi_mem"
    est = pricing.estimate_elasticity_iv(df, "ngoi_mem", min_obs=300)
    assert est.value <= C.ELASTICITY_CAP
    if not est.used_fallback:
        assert est.reason in (None, "clipped_to_bounds")


def test_estimate_exponential_alpha_iv_returns_positive_alpha_for_downward_sloping_demand():
    df = _endogenous_price_demand_panel(true_eps=2.2)
    df["seat_type"] = "ngoi_mem"
    est = pricing.estimate_exponential_alpha_iv(df, "ngoi_mem", min_obs=300)
    # alpha (mô hình cộng) không cùng thang đo với eps (mô hình nhân) nhưng phải > 0
    # (cầu giảm khi giá tăng) khi ước lượng không rơi vào fallback.
    if not est.used_fallback:
        assert est.value > 0


def test_estimate_elasticity_public_api_smoke_on_real_datagen():
    """Chạy trên dữ liệu mô phỏng thật của datagen.simulate() (như scripts/train.py) —
    đảm bảo toàn bộ pipeline AI-09 -> AI-15 không vỡ trên dữ liệu thực tế của hệ thống."""
    from datetime import date

    from ai_service import datagen

    sim = datagen.simulate(start=date(2024, 1, 1), days=60)
    eps = pricing.estimate_elasticity(sim["history"])

    assert set(eps.keys()) == set(C.SEAT_TYPES)
    for stype in C.SEAT_TYPES:
        assert C.ELASTICITY_FLOOR <= eps[stype] <= C.ELASTICITY_CAP


# ============================================================
# AI-11 — c_j = Σ a·π
# ============================================================


def test_compute_opportunity_cost_sums_bid_price_across_segments():
    od = _od(segments=(0, 1, 2))
    bid_prices = {(0, "ngoi_mem"): 10.0, (1, "ngoi_mem"): 20.0, (2, "ngoi_mem"): 5.0}
    assert pricing.compute_opportunity_cost(od, bid_prices) == pytest.approx(35.0)


def test_compute_opportunity_cost_missing_segment_defaults_to_zero():
    od = _od(segments=(0, 1))
    bid_prices = {(0, "ngoi_mem"): 10.0}  # thiếu seg 1
    assert pricing.compute_opportunity_cost(od, bid_prices) == pytest.approx(10.0)


def test_compute_opportunity_cost_ignores_other_seat_type():
    od = _od(seat_type="ngoi_mem", segments=(0,))
    bid_prices = {(0, "ngoi_mem"): 10.0, (0, "giuong_nam_k6"): 999.0}
    assert pricing.compute_opportunity_cost(od, bid_prices) == pytest.approx(10.0)


# ============================================================
# AI-16.1 — Công thức markup ε/(ε−1)
# ============================================================


def test_markup_multiplicative_formula():
    assert pricing.markup_multiplicative(80_000, 1.8) == pytest.approx(80_000 * 1.8 / 0.8)


def test_markup_multiplicative_zero_when_no_opportunity_cost():
    assert pricing.markup_multiplicative(0.0, 1.8) == 0.0
    assert pricing.markup_multiplicative(-5.0, 1.8) == 0.0


def test_markup_multiplicative_raises_when_epsilon_not_greater_than_one():
    with pytest.raises(ValueError):
        pricing.markup_multiplicative(100.0, 1.0)
    with pytest.raises(ValueError):
        pricing.markup_multiplicative(100.0, 0.5)


# ============================================================
# AI-16.2 — Sinh explanation (nút cổ chai, tải)
# ============================================================


def test_build_explanation_identifies_bottleneck_as_max_bid_price_segment():
    od = _od(segments=(0, 1))
    bid_prices = {(0, "ngoi_mem"): 10.0, (1, "ngoi_mem"): 90.0}
    exp = pricing.build_explanation(od, bid_prices, epsilon=1.8)
    assert exp["bottleneck_segment"] == 1
    assert exp["segment_pi"] == {0: 10.0, 1: 90.0}


def test_build_explanation_includes_load_pct_when_segment_load_given():
    od = _od(segments=(0, 1))
    bid_prices = {(0, "ngoi_mem"): 10.0, (1, "ngoi_mem"): 90.0}
    segment_load = {(0, "ngoi_mem"): 0.3, (1, "ngoi_mem"): 0.875}
    exp = pricing.build_explanation(od, bid_prices, epsilon=1.8, segment_load=segment_load)
    assert exp["bottleneck_load_pct"] == pytest.approx(87.5)


def test_build_explanation_load_pct_none_without_segment_load():
    od = _od(segments=(0,))
    bid_prices = {(0, "ngoi_mem"): 10.0}
    exp = pricing.build_explanation(od, bid_prices, epsilon=1.8)
    assert exp["bottleneck_load_pct"] is None


def test_build_explanation_load_pct_none_when_bottleneck_missing_from_load_map():
    od = _od(segments=(0,))
    bid_prices = {(0, "ngoi_mem"): 10.0}
    exp = pricing.build_explanation(od, bid_prices, epsilon=1.8, segment_load={(1, "ngoi_mem"): 0.5})
    assert exp["bottleneck_load_pct"] is None


# ============================================================
# price_od — end-to-end
# ============================================================


def test_price_od_end_to_end_with_segment_load():
    od = _od(segments=(0, 1), base_price=100_000)
    bid_prices = {(0, "ngoi_mem"): 50_000, (1, "ngoi_mem"): 30_000}
    segment_load = {(0, "ngoi_mem"): 0.9, (1, "ngoi_mem"): 0.4}
    q = pricing.price_od(od, bid_prices, {"ngoi_mem": 1.8}, segment_load=segment_load)

    oc = 80_000
    assert q["opportunity_cost"] == pytest.approx(oc)
    assert q["proposed_price"] == round(oc * 1.8 / 0.8, 0)
    assert q["explanation"]["bottleneck_segment"] == 0
    assert q["explanation"]["bottleneck_load_pct"] == pytest.approx(90.0)


def test_price_od_floors_at_base_price_when_opportunity_cost_low():
    od = _od(base_price=500_000)
    q = pricing.price_od(od, {(0, "ngoi_mem"): 1_000}, {"ngoi_mem": 1.8})
    assert q["proposed_price"] == 500_000


def test_price_od_caps_at_max_surge():
    od = _od(base_price=100_000)
    q = pricing.price_od(od, {(0, "ngoi_mem"): 10_000_000}, {"ngoi_mem": 1.8})
    assert q["proposed_price"] == pytest.approx(100_000 * C.MAX_SURGE)


def test_price_od_policy_guard_blocks_and_reports_min_price():
    od = _od(base_price=100_000)
    q = pricing.price_od(
        od,
        {(0, "ngoi_mem"): 50_000},
        {"ngoi_mem": 1.8},
        policy={"min_price": 900_000, "max_price": 999_999},
    )
    assert q["decision"] == "blocked"
    assert q["final_price"] == 900_000


def test_price_od_policy_guard_within_range_stays_accepted():
    od = _od(base_price=100_000)
    q = pricing.price_od(
        od,
        {(0, "ngoi_mem"): 10_000},
        {"ngoi_mem": 1.8},
        policy={"min_price": 1, "max_price": 999_999_999},
    )
    assert q["decision"] == "accepted"
    assert q["final_price"] == q["proposed_price"]


def test_explanation_shape():
    od = _od(segments=(0,), base_price=100_000)
    q = pricing.price_od(od, {(0, "ngoi_mem"): 50_000}, {"ngoi_mem": 1.8})
    exp = q["explanation"]
    assert set(exp.keys()) == {
        "bottleneck_segment",
        "segment_pi",
        "elasticity",
        "base_price",
        "bottleneck_load_pct",
    }
    assert exp["elasticity"] == 1.8
    assert exp["base_price"] == 100_000


def test_estimate_elasticity_fallback_when_insufficient_data():
    empty = pd.DataFrame(
        columns=[
            "seat_type",
            "willing",
            "shown_price",
            "od_id",
            "dow",
            "month",
            "is_holiday",
            "is_tet",
            "distance_km",
        ]
    )
    eps = pricing.estimate_elasticity(empty)
    for stype in C.SEAT_TYPES:
        assert eps[stype] == C.ELASTICITY[stype]


def test_estimate_elasticity_is_clipped_to_floor_and_cap():
    # Dữ liệu tổng hợp: giá không đổi trong từng OD -> slope ~0 -> fallback về config,
    # nhưng vẫn phải nằm trong [FLOOR, CAP] theo hợp đồng của hàm.
    rows = []
    for od_id in range(5):
        for i in range(150):
            rows.append(
                dict(
                    seat_type="ngoi_mem",
                    od_id=od_id,
                    shown_price=100_000 + i,
                    willing=1,
                    dow=0,
                    month=1,
                    is_holiday=0,
                    is_tet=0,
                    distance_km=100.0,
                )
            )
    hist = pd.DataFrame(rows)
    eps = pricing.estimate_elasticity(hist)
    assert C.ELASTICITY_FLOOR <= eps["ngoi_mem"] <= C.ELASTICITY_CAP
