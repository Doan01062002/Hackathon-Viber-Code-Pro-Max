import subprocess
import sys

from fastapi import FastAPI

from index import app as vercel_app


def test_vercel_entrypoint_exports_complete_fastapi_app() -> None:
    assert isinstance(vercel_app, FastAPI)

    route_paths = set(vercel_app.openapi()["paths"])
    assert "/health" in route_paths
    assert "/api/v1/chat" in route_paths
    assert "/api/v1/ai/forecast" in route_paths


def test_fastapi_startup_does_not_import_heavy_ai_engine() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import index; print('ai_service.engine' in sys.modules)",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip().splitlines()[0] == "False"
