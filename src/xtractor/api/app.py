from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from xtractor.api.routers.extract import router as extract_router
from xtractor.config.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Document Xtractor", version="1.2.5")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_cors or ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(extract_router)

    @app.get("/", tags=["health"], summary="Return service health state")
    async def healthcheck() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "document-xtractor",
            "version": app.version,
            "environment": settings.environment,
        }

    return app


app = create_app()


__all__ = ["app", "create_app"]
