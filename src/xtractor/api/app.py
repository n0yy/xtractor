from __future__ import annotations

from fastapi import FastAPI

from xtractor.api.routers.extract import router as extract_router
from xtractor.config.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Document Xtractor", version="1.2.5")
    app.include_router(extract_router)

    @app.get("/health", tags=["health"])
    def healthcheck() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()


__all__ = ["app", "create_app"]
