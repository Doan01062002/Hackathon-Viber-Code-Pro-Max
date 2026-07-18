from pydantic import BaseModel, Field


class TableSummary(BaseModel):
    name: str
    column_count: int
    row_count: int | None = None


class DatabaseSummaryResponse(BaseModel):
    table_count: int
    tables: list[TableSummary]


class DatabaseTableCountResponse(BaseModel):
    table_count: int


class TableDataResponse(BaseModel):
    table_name: str
    columns: list[str]
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
    row_count: int
    rows: list[dict[str, object | None]]


class TableCountResponse(BaseModel):
    table_name: str
    row_count: int
