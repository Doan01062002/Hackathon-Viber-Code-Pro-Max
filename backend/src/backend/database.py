from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """Create one connection pool for the lifetime of the process."""
    database_url = get_settings().database_url
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that commits or rolls back one unit of work."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_database_status() -> str:
    """Return a health value without exposing connection details."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return "unavailable"
    return "ok"


def dispose_engine() -> None:
    if get_engine.cache_info().currsize:
        get_engine().dispose()

