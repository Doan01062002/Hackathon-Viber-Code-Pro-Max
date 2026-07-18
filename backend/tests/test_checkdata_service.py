import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text

from backend.services.checkdata_service import CheckDataService


@pytest.fixture
def service():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE stations (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"))
        connection.execute(text("INSERT INTO stations (id, name) VALUES (1, 'Sai Gon'), (2, 'Ha Noi')"))
    return CheckDataService(engine)


def test_checkdata_service_lists_tables_with_counts(service):
    summary = service.list_tables()

    assert summary.table_count == 1
    assert summary.tables[0].name == "stations"
    assert summary.tables[0].column_count == 2
    assert summary.tables[0].row_count == 2


def test_checkdata_service_counts_tables_without_counting_rows(service):
    summary = service.count_tables()

    assert summary.table_count == 1


def test_checkdata_service_lists_tables_without_counts(service):
    summary = service.list_tables(include_counts=False)

    assert summary.table_count == 1
    assert summary.tables[0].name == "stations"
    assert summary.tables[0].column_count == 2
    assert summary.tables[0].row_count is None


def test_checkdata_service_reads_rows(service):
    data = service.get_table_data("stations", limit=1, offset=1)

    assert data.columns == ["id", "name"]
    assert data.row_count == 1
    assert data.rows == [{"id": 2, "name": "Ha Noi"}]


def test_checkdata_service_counts_rows(service):
    count = service.count_rows("stations")

    assert count.row_count == 2


def test_checkdata_service_rejects_unknown_table(service):
    with pytest.raises(HTTPException) as exc_info:
        service.get_table_data("stations; DROP TABLE stations")

    assert exc_info.value.status_code == 404
