import pytest
from ai_service.engine import AIEngine
from ai_service.schemas import ForecastRequest, OptimizeRequest, PriceRequest


@pytest.fixture
def engine():
    return AIEngine()


def test_health(engine):
    """Kiểm tra trạng thái engine."""
    assert engine.health()["status"] == "ok"


def test_forecast(engine):
    """Kiểm tra Khối 1 — dự báo nhu cầu."""
    data = engine.forecast(ForecastRequest(service_date="2026-07-20"))
    assert data.service_date == "2026-07-20"
    assert data.model_version
    assert len(data.items) > 0
    assert data.items[0].origin
    assert data.items[0].dest


def test_optimize(engine):
    """Kiểm tra Khối 2 — tối ưu chặng (DLP)."""
    data = engine.optimize(OptimizeRequest(service_date="2026-07-20"))
    assert data.service_date == "2026-07-20"
    assert data.solve_ms >= 0
    assert data.revenue_lp >= 0
    assert isinstance(data.bid_prices, list)


def test_price_without_policy(engine):
    """Kiểm tra Khối 3 — tính giá không kèm chính sách."""
    data = engine.price(PriceRequest(od_id=1, service_date="2026-07-20"))
    assert data.od_id == 1
    assert data.final_price >= 0
    assert data.opportunity_cost >= 0


def test_price_with_policy(engine):
    """Kiểm tra Khối 3 — tính giá có trần/sàn."""
    data = engine.price(
        PriceRequest(od_id=1, service_date="2026-07-20", min_price=200000.0, max_price=600000.0)
    )
    assert data.od_id == 1
    assert data.final_price >= 200000.0
    assert data.final_price <= 600000.0
