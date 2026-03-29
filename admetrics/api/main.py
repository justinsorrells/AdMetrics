"""FastAPI application entrypoint."""

from fastapi import FastAPI

from admetrics.api.routes.campaigns import router as campaign_router
from admetrics.api.routes.health import router as health_router
from admetrics.api.routes.metrics import router as metrics_router
from admetrics.api.routes.reports import router as reports_router
from admetrics.config import Settings, get_settings
from admetrics.db import models  # noqa: F401
from admetrics.db.session import DatabaseSessionManager


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure a FastAPI application instance."""

    app_settings = settings or get_settings()
    app = FastAPI(
        title=app_settings.app_name,
        version="1.0.0",
        description="REST API for ingesting and reporting campaign performance metrics.",
    )
    app.state.settings = app_settings
    app.state.db = DatabaseSessionManager(app_settings.database_url)
    app.state.db.create_tables()

    app.include_router(health_router)
    app.include_router(campaign_router)
    app.include_router(metrics_router)
    app.include_router(reports_router)

    return app


app = create_app()
