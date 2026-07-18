import os

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import hashlib
import sys
import types
from pathlib import Path


class MockXXHash:
    def __init__(self, data=b""):
        self.data = data

    def digest(self):
        return hashlib.md5(self.data).digest()

    def hexdigest(self):
        return hashlib.md5(self.data).hexdigest()


def xxh3_128(data=b"", seed=0):
    if isinstance(data, str):
        data = data.encode()
    return MockXXHash(data)


def xxh3_128_hexdigest(data, seed=0):
    if isinstance(data, str):
        data = data.encode()
    return hashlib.md5(data).hexdigest()


xxhash_mock = types.ModuleType("xxhash")
xxhash_mock.xxh3_128 = xxh3_128
xxhash_mock.xxh3_128_hexdigest = xxh3_128_hexdigest

sys.modules["xxhash"] = xxhash_mock

import psycopg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url

from backend.controllers.chat_controller import get_chat_service
from backend.database import dispose_engine, get_database_status
from backend.main import create_app
from backend.models.chat import ChatMessage


@pytest.fixture(scope="session", autouse=True)
def bootstrap_postgres_test_database():
    """Build a fresh, deterministic database only for the opt-in CI test service."""
    if os.getenv("SRRM_BOOTSTRAP_TEST_DB") != "1":
        yield
        return

    database_url = os.getenv("DATABASE_URL", "")
    url = make_url(database_url)
    database_name = url.database or ""
    allowed_hosts = {"127.0.0.1", "localhost", "::1"}
    if (
        not url.drivername.startswith("postgresql")
        or url.host not in allowed_hosts
        or not database_name.endswith("_test")
    ):
        raise RuntimeError(
            "Refusing to bootstrap a database that is not local PostgreSQL with a *_test name"
        )

    repository_root = Path(__file__).resolve().parents[2]
    schema_sql = (repository_root / "schema.sql").read_text(encoding="utf-8")
    seed_sql = (Path(__file__).resolve().parent / "postgres_seed.sql").read_text(
        encoding="utf-8"
    )
    conninfo = url.set(drivername="postgresql").render_as_string(hide_password=False)

    with psycopg.connect(conninfo) as connection:
        connection.execute("DROP SCHEMA IF EXISTS public CASCADE")
        connection.execute("CREATE SCHEMA public")
        connection.execute(schema_sql, prepare=False)
        connection.execute(seed_sql, prepare=False)
        fixture_is_valid = connection.execute(
            """
            SELECT
                (SELECT code FROM stations WHERE id = 1) = 'HAN'
                AND (SELECT service_date FROM trips WHERE id = 1) = DATE '2024-01-01'
                AND EXISTS (
                    SELECT 1
                    FROM od_products
                    WHERE id = 1
                      AND trip_id = 1
                      AND origin_station_id = 1
                      AND destination_station_id = 2
                      AND seat_type = 'ngoi_mem'
                )
                AND (SELECT COUNT(*) FROM segments WHERE trip_id = 1) = 19
                AND (
                    SELECT COUNT(*)
                    FROM seats
                    WHERE trip_id = 1 AND coach_no = '01' AND seat_type = 'ngoi_mem'
                ) = 64
                AND (
                    SELECT COUNT(*)
                    FROM od_products
                    WHERE trip_id = 1 AND origin_station_id = 1 AND destination_station_id = 2
                ) = 2
            """
        ).fetchone()
        if fixture_is_valid is None or fixture_is_valid[0] is not True:
            raise RuntimeError("PostgreSQL test seed does not satisfy its required invariants")

    yield
    dispose_engine()


class FakeChatService:
    """Service giả — test controller mà không gọi AI agent thật."""

    async def send_message(self, message: str) -> ChatMessage:
        return ChatMessage(response=f"echo: {message}", analysis="fake")


@pytest.fixture
def app():
    app = create_app()
    app.dependency_overrides[get_chat_service] = FakeChatService
    app.dependency_overrides[get_database_status] = lambda: "ok"
    return app


@pytest_asyncio.fixture
async def client(app):
    """Async HTTP client for testing API endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
