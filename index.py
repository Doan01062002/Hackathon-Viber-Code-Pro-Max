"""Vercel ASGI entrypoint for the SRRM backend and in-process AI engine."""

from backend.main import app

__all__ = ["app"]
