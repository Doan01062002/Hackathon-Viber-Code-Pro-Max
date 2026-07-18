from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import MetaData, Table, func, inspect, select
from sqlalchemy.engine import Engine

from backend.database import get_engine
from backend.views.checkdata_view import (
    DatabaseSummaryResponse,
    DatabaseTableCountResponse,
    TableCountResponse,
    TableDataResponse,
    TableSummary,
)


class CheckDataService:
    def __init__(self, engine: Engine | None = None) -> None:
        self.engine = engine or get_engine()

    def count_tables(self) -> DatabaseTableCountResponse:
        inspector = inspect(self.engine)
        return DatabaseTableCountResponse(table_count=len(inspector.get_table_names()))

    def list_tables(self, include_counts: bool = True) -> DatabaseSummaryResponse:
        inspector = inspect(self.engine)
        table_names = sorted(inspector.get_table_names())
        summaries: list[TableSummary] = []

        for table_name in table_names:
            columns = inspector.get_columns(table_name)
            row_count = self.count_rows(table_name).row_count if include_counts else None
            summaries.append(
                TableSummary(
                    name=table_name,
                    column_count=len(columns),
                    row_count=row_count,
                )
            )

        return DatabaseSummaryResponse(table_count=len(table_names), tables=summaries)

    def get_table_data(self, table_name: str, limit: int = 20, offset: int = 0) -> TableDataResponse:
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        table = self._load_table(table_name)

        with self.engine.connect() as connection:
            result = connection.execute(select(table).limit(limit).offset(offset)).mappings()
            rows = [{key: self._json_safe(value) for key, value in row.items()} for row in result]

        return TableDataResponse(
            table_name=table.name,
            columns=[column.name for column in table.columns],
            limit=limit,
            offset=offset,
            row_count=len(rows),
            rows=rows,
        )

    def count_rows(self, table_name: str) -> TableCountResponse:
        table = self._load_table(table_name)
        with self.engine.connect() as connection:
            row_count = connection.scalar(select(func.count()).select_from(table))

        return TableCountResponse(table_name=table.name, row_count=int(row_count or 0))

    def _load_table(self, table_name: str) -> Table:
        inspector = inspect(self.engine)
        table_names = set(inspector.get_table_names())
        if table_name not in table_names:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

        metadata = MetaData()
        return Table(table_name, metadata, autoload_with=self.engine)

    @staticmethod
    def _json_safe(value: object | None) -> object | None:
        if value is None or isinstance(value, str | int | float | bool):
            return value
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, datetime | date):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, bytes):
            return value.hex()
        return str(value)
