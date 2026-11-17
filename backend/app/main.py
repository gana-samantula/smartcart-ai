"""Application factory and the ASGI entrypoint (`app.main:app`)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.health import router as health_router
from app.api.v1.router import api_router as v1_router
from app.core.config import Settings, get_settings
from app.core.database import create_db_engine, create_session_factory
from app.core.errors import register_exception_handlers
from app.core.logging_config import configure_logging
from app.core.middleware import attach_request_id
from app.core.rate_limit import RateLimiter
from app.integrations.email import build_email_sender


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build a configured application.

    Tests pass explicit settings. The ASGI server uses the environment.
    """
    resolved = settings or get_settings()
    configure_logging(resolved.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        app.state.engine.dispose()

    is_production = resolved.environment == "production"
    app = FastAPI(
        title=resolved.app_name,
        version=__version__,
        lifespan=lifespan,
        docs_url=None if is_production else "/docs",
        redoc_url=None,
        openapi_url=None if is_production else "/openapi.json",
    )
    app.state.settings = resolved
    app.state.engine = create_db_engine(resolved)
    app.state.session_factory = create_session_factory(app.state.engine)
    app.state.email_sender = build_email_sender(resolved)
    app.state.rate_limiter = RateLimiter()

    app.middleware("http")(attach_request_id)
    if resolved.cors_allowed_origins:
        # Bearer tokens travel in headers, so cookies and credentialed CORS are not needed.
        app.add_middleware(
            CORSMiddleware,
            allow_origins=resolved.cors_allowed_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        )

    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(v1_router)
    return app


app = create_app()
