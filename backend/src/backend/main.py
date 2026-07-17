from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.controllers import api_router
from backend.controllers.health_controller import router as health_router
from backend.database import dispose_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    print(f"Starting {settings.app_name} in {settings.app_env} mode")

    worker = None
    try:
        from backend.worker import EventWorker

        worker = EventWorker(debounce_seconds=5.0)
        worker.start()
    except Exception as e:
        print(f"Warning: Could not start EventWorker: {str(e)}")

    yield

    if worker:
        try:
            worker.stop()
        except Exception:
            pass

    dispose_engine()
    print("Shutting down...")


def create_app() -> FastAPI:
    """App factory — test dựng được instance sạch, không dùng global."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="AI Agent built with LangGraph",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
