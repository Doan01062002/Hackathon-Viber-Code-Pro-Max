import os
import sys

import pytest
from fastapi.testclient import TestClient

# Thêm thư mục ai vào sys.path để import ai_service
ai_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ai_path not in sys.path:
    sys.path.insert(0, ai_path)

from ai_service.app import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    """Kiểm tra endpoint health của ai-service."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_forecast(client):
    """Kiểm tra endpoint dự báo /internal/forecast."""
    response = client.post("/internal/forecast", json={"service_date": "2026-07-20"})
    assert response.status_code == 200
    data = response.json()
    assert data["service_date"] == "2026-07-20"
    assert "model_version" in data
    assert len(data["items"]) > 0
    assert "origin" in data["items"][0]
    assert "dest" in data["items"][0]


def test_optimize(client):
    """Kiểm tra endpoint tối ưu /internal/optimize."""
    response = client.post("/internal/optimize", json={"service_date": "2026-07-20"})
    assert response.status_code == 200
    data = response.json()
    assert data["service_date"] == "2026-07-20"
    assert "solve_ms" in data
    assert "revenue_lp" in data
    assert isinstance(data["bid_prices"], list)


def test_price_without_policy(client):
    """Kiểm tra endpoint tính giá /internal/price không kèm chính sách."""
    response = client.post("/internal/price", json={
        "od_id": 1,
        "service_date": "2026-07-20"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["od_id"] == 1
    assert "final_price" in data
    assert "opportunity_cost" in data


def test_price_with_policy(client):
    """Kiểm tra endpoint tính giá /internal/price có trần/sàn."""
    response = client.post("/internal/price", json={
        "od_id": 1,
        "service_date": "2026-07-20",
        "min_price": 200000.0,
        "max_price": 600000.0
    })
    assert response.status_code == 200
    data = response.json()
    assert data["od_id"] == 1
    assert data["final_price"] >= 200000.0
    assert data["final_price"] <= 600000.0
