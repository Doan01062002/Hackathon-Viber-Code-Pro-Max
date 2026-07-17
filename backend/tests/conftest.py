import os

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import hashlib
import sys
import types


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

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.database import get_database_status
from backend.main import create_app


@pytest.fixture
def app():
    app = create_app()
    app.dependency_overrides[get_database_status] = lambda: "ok"
    return app


@pytest_asyncio.fixture
async def client(app):
    """Async HTTP client for testing API endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
