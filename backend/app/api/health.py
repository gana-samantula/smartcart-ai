"""Liveness and readiness probes. Unversioned, served at the root."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_engine
from app.core.errors import ServiceUnavailableError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness: the process is serving requests")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready", summary="Readiness: dependencies are reachable")
def readiness(engine: Annotated[Engine, Depends(get_engine)]) -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        # The driver message can include connection details, so log only the type.
        logger.warning("Readiness check failed", extra={"error_type": type(exc).__name__})
        raise ServiceUnavailableError("The database is not reachable.") from exc
    return {"status": "ready", "database": "ok"}
