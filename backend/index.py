"""Serverless entrypoint exposing the shared FastAPI application."""

from backend.main import app

__all__ = ["app"]
