FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./pyproject.toml
COPY src/ ./src/
COPY ai_service/ ./ai_service/
COPY models/ ./models/

RUN pip install --no-cache-dir .

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8001

CMD ["uvicorn", "ai_service.app:app", "--host", "0.0.0.0", "--port", "8001"]
