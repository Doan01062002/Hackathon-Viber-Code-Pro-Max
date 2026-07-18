# Backend API Docs

The backend exposes Swagger UI at:

```text
http://localhost:8000/docs
```

Use this page to inspect all backend API URLs, request bodies, query parameters, response schemas, and to try calls directly from the browser.

Related documentation endpoints:

- `GET /docs` - Swagger UI.
- `GET /openapi.json` - OpenAPI schema used by Swagger.
- `GET /redoc` - ReDoc view.

The Swagger page is configured in `backend/src/backend/main.py` through FastAPI's built-in OpenAPI support.
