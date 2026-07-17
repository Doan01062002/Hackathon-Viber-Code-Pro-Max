"""Test Khối 3 — pricing markup + diễn giải (ai_service/pricing.py)."""

import pandas as pd
import pytest
from ai_service import config as C
from ai_service import pricing


def _od(seat_type="ngoi_mem", segments=(0,), base_price=100_000, od_id=1):
    return dict(od_id=od_id, seat_type=seat_type, segments=list(segments), base_price=base_price)


def test_markup_formula_matches_ec_over_e_minus_1():
    od = _od(segments=(0, 1), base_price=100_000)
    bid_prices = {(0, "ngoi_mem"): 50_000, (1, "ngoi_mem"): 30_000}
    eps = {"ngoi_mem": 1.8}

    q = pricing.price_od(od, bid_prices, eps)

    oc = 80_000
    expected = oc * 1.8 / (1.8 - 1)
    assert q["opportunity_cost"] == pytest.approx(oc)
    assert q["proposed_price"] == round(expected, 0)
    assert q["decision"] == "accepted"


def test_proposed_price_floors_at_base_price_when_opportunity_cost_low():
    od = _od(base_price=500_000)
    q = pricing.price_od(od, {(0, "ngoi_mem"): 1_000}, {"ngoi_mem": 1.8})
    assert q["proposed_price"] == 500_000


def test_proposed_price_capped_at_max_surge():
    od = _od(base_price=100_000)
    q = pricing.price_od(od, {(0, "ngoi_mem"): 10_000_000}, {"ngoi_mem": 1.8})
    assert q["proposed_price"] == pytest.approx(100_000 * C.MAX_SURGE)


def test_bottleneck_segment_is_the_one_with_max_bid_price():
    od = _od(segments=(0, 1), base_price=100_000)
    bid_prices = {(0, "ngoi_mem"): 10_000, (1, "ngoi_mem"): 90_000}
    q = pricing.price_od(od, bid_prices, {"ngoi_mem": 1.8})
    assert q["explanation"]["bottleneck_segment"] == 1


def test_zero_opportunity_cost_gives_zero_markup_price():
    od = _od(base_price=100_000)
    q = pricing.price_od(od, {}, {"ngoi_mem": 1.8})
    assert q["opportunity_cost"] == 0.0
    # markup_price=0 nhưng vẫn floor ở base_price
    assert q["proposed_price"] == 100_000


def test_policy_guard_blocks_and_reports_min_price():
    od = _od(base_price=100_000)
    q = pricing.price_od(
        od,
        {(0, "ngoi_mem"): 50_000},
        {"ngoi_mem": 1.8},
        policy={"min_price": 900_000, "max_price": 999_999},
    )
    assert q["decision"] == "blocked"
    assert q["final_price"] == 900_000


def test_policy_guard_within_range_stays_accepted():
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
    assert set(exp.keys()) == {"bottleneck_segment", "segment_pi", "elasticity", "base_price"}
    assert exp["elasticity"] == 1.8
    assert exp["base_price"] == 100_000


def test_estimate_elasticity_fallback_when_insufficient_data():
    empty = pd.DataFrame({"seat_type": [], "willing": [], "shown_price": [], "od_id": []})
    eps = pricing.estimate_elasticity(empty)
    for stype in C.SEAT_TYPES:
        assert eps[stype] == C.ELASTICITY[stype]


def test_estimate_elasticity_is_clipped_to_floor_and_cap():
    # Dữ liệu tổng hợp: giá không đổi trong từng OD -> slope ~0 -> fallback về config,
    # nhưng vẫn phải nằm trong [FLOOR, CAP] theo hợp đồng của hàm.
    rows = []
    for od_id in range(5):
        for i in range(150):
            rows.append(dict(seat_type="ngoi_mem", od_id=od_id, shown_price=100_000 + i, willing=1))
    hist = pd.DataFrame(rows)
    eps = pricing.estimate_elasticity(hist)
    assert C.ELASTICITY_FLOOR <= eps["ngoi_mem"] <= C.ELASTICITY_CAP
