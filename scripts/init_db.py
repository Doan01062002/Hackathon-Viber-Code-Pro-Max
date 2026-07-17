"""Initialize the PostgreSQL schema configured by DATABASE_URL."""

from pathlib import Path

import psycopg
from sqlalchemy.engine import make_url

from backend.config import get_settings

ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT_DIR / "schema.sql"
EXPECTED_TABLES = {
    "audit_logs",
    "bid_prices",
    "bookings",
    "calendar_features",
    "demand_forecasts",
    "fare_classes",
    "gap_combinations",
    "od_product_segments",
    "od_products",
    "price_policies",
    "price_quotes",
    "quotas",
    "search_logs",
    "seat_types",
    "seats",
    "segment_capacities",
    "segment_inventory",
    "segments",
    "stations",
    "trains",
    "trips",
}


def get_conninfo() -> str:
    url = make_url(get_settings().database_url)
    if not url.drivername.startswith("postgresql"):
        raise RuntimeError("schema.sql can only initialize PostgreSQL")
    return url.set(drivername="postgresql").render_as_string(hide_password=False)


def main() -> None:
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    with psycopg.connect(get_conninfo()) as connection:
        existing_rows = connection.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        ).fetchall()
        existing_tables = {row[0] for row in existing_rows} & EXPECTED_TABLES

        if existing_tables == EXPECTED_TABLES:
            print(f"Schema already initialized ({len(EXPECTED_TABLES)} tables).")
            return
        if existing_tables:
            names = ", ".join(sorted(existing_tables))
            raise RuntimeError(f"Partial schema detected; refusing to continue: {names}")

        connection.execute(schema_sql, prepare=False)

    print(f"Schema initialized successfully ({len(EXPECTED_TABLES)} tables).")


if __name__ == "__main__":
    main()
