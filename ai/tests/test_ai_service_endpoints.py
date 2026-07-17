"""Test contract cho ai-service: /internal/forecast, /internal/optimize, /internal/price.

Dùng model đã train sẵn tại ai/models/model.pkl (chạy `python scripts/train.py`
trước nếu file chưa tồn tại — xem README/AGENTS.md).
"""

import os

import pytest
from ai_service.app import MODEL_PATH, app
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(
    not os.path.exists(MODEL_PATH),
    reason=f"Chưa có model tại {MODEL_PATH} — chạy `python scripts/train.py` trước.",
)

SERVICE_DATE = "2024-03-01"


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_forecast_endpoint_returns_items(client):
    r = client.post("/internal/forecast", json={"service_date": SERVICE_DATE})
    assert r.status_code == 200
    body = r.json()
    assert body["service_date"] == SERVICE_DATE
    assert len(body["items"]) > 0
    item = body["items"][0]
    assert item["p10"] <= item["p50"] <= item["p90"]
    assert item["lambda_hat"] >= 0


def test_forecast_endpoint_rejects_bad_date(client):
    r = client.post("/internal/forecast", json={"service_date": "not-a-date"})
    assert r.status_code == 422 or r.status_code == 400


def test_optimize_endpoint_returns_valid_schema(client):
    r = client.post("/internal/optimize", json={"service_date": SERVICE_DATE})
    assert r.status_code == 200
    body = r.json()
    assert body["run_version"]
    assert isinstance(body["warm_started"], bool)
    assert body["revenue_lp"] >= 0
    assert body["n_od"] > 0
    for bp in body["bid_prices"]:
        assert bp["bid_price"] >= 0


def test_optimize_second_call_warm_starts_with_same_run_version(client):
    first = client.post("/internal/optimize", json={"service_date": SERVICE_DATE}).json()
    second = client.post("/internal/optimize", json={"service_date": SERVICE_DATE}).json()

    assert first["warm_started"] is False
    assert second["warm_started"] is True
    assert second["run_version"] == first["run_version"]


def test_optimize_force_resolve_bypasses_cache(client):
    first = client.post("/internal/optimize", json={"service_date": SERVICE_DATE}).json()
    forced = client.post("/internal/optimize", json={"service_date": SERVICE_DATE, "force_resolve": True}).json()

    assert forced["warm_started"] is False
    assert forced["run_version"] != first["run_version"]


def test_price_endpoint_valid_od(client):
    r = client.post("/internal/price", json={"od_id": 0, "service_date": SERVICE_DATE})
    assert r.status_code == 200
    body = r.json()
    assert body["od_id"] == 0
    assert body["final_price"] >= 0
    assert body["decision"] in ("accepted", "blocked")
    assert "bottleneck_segment" in body["explanation"]
    assert "elasticity" in body["explanation"]


def test_price_endpoint_od_not_found(client):
    r = client.post("/internal/price", json={"od_id": 999_999, "service_date": SERVICE_DATE})
    assert r.status_code == 404


def test_price_endpoint_policy_guard_blocks(client):
    r = client.post(
        "/internal/price",
        json={
            "od_id": 0,
            "service_date": SERVICE_DATE,
            "min_price": 999_999_999,
            "max_price": 999_999_999,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "blocked"
    assert body["final_price"] == 999_999_999
