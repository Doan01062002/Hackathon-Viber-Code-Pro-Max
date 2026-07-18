import pytest

from backend.controllers.checkdata_controller import get_checkdata_service
from backend.views.checkdata_view import (
    DatabaseSummaryResponse,
    DatabaseTableCountResponse,
    TableCountResponse,
    TableDataResponse,
    TableSummary,
)


class FakeCheckDataService:
    def count_tables(self) -> DatabaseTableCountResponse:
        return DatabaseTableCountResponse(table_count=1)

    def list_tables(self, include_counts: bool = True) -> DatabaseSummaryResponse:
        return DatabaseSummaryResponse(
            table_count=1,
            tables=[TableSummary(name="stations", column_count=2, row_count=2 if include_counts else None)],
        )

    def get_table_data(self, table_name: str, limit: int = 20, offset: int = 0) -> TableDataResponse:
        return TableDataResponse(
            table_name=table_name,
            columns=["id", "name"],
            limit=limit,
            offset=offset,
            row_count=1,
            rows=[{"id": 1, "name": "Sai Gon"}],
        )

    def count_rows(self, table_name: str) -> TableCountResponse:
        return TableCountResponse(table_name=table_name, row_count=2)


@pytest.fixture(autouse=True)
def override_checkdata_service(app):
    app.dependency_overrides[get_checkdata_service] = FakeCheckDataService
    yield
    app.dependency_overrides.pop(get_checkdata_service, None)


@pytest.mark.asyncio
async def test_checkdata_page(client):
    response = await client.get("/checkdata")

    assert response.status_code == 200
    assert "SRRM Database Check" in response.text
    assert "/checkdata/api/tables" in response.text
    assert "Công cụ xem database nhanh" in response.text
    assert "Nhập tên bảng rồi bấm Xem dữ liệu" in response.text


@pytest.mark.asyncio
async def test_checkdata_counts_tables_only(client):
    response = await client.get("/checkdata/api/table-count")

    assert response.status_code == 200
    assert response.json() == {"table_count": 1}


@pytest.mark.asyncio
async def test_checkdata_lists_tables(client):
    response = await client.get("/checkdata/api/tables?include_counts=false")

    assert response.status_code == 200
    assert response.json() == {
        "table_count": 1,
        "tables": [{"name": "stations", "column_count": 2, "row_count": None}],
    }


@pytest.mark.asyncio
async def test_checkdata_reads_table_data(client):
    response = await client.get("/checkdata/api/tables/stations?limit=10&offset=0")

    assert response.status_code == 200
    assert response.json()["columns"] == ["id", "name"]
    assert response.json()["rows"] == [{"id": 1, "name": "Sai Gon"}]


@pytest.mark.asyncio
async def test_checkdata_counts_table_rows(client):
    response = await client.get("/checkdata/api/tables/stations/count")

    assert response.status_code == 200
    assert response.json() == {"table_name": "stations", "row_count": 2}
