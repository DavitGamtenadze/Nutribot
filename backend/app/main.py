import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.routes import router as api_router
from app.config import get_settings
from app.db.session import engine

logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    os.makedirs(settings.upload_dir, exist_ok=True)
    if settings.database_url.startswith("sqlite"):
        from app.db import models as _models  # noqa: F401
        from app.db.base import Base

        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Nutribot API",
    version="0.1.0",
    description="LLM-powered nutrition guide with tool calling + structured outputs.",
    lifespan=lifespan,
)

# StaticFiles validates the directory at import time, so this must exist
# before mounting on serverless cold starts.
os.makedirs(settings.upload_dir, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type"],
)


def _format_validation_detail(errors: list) -> str:
    """Turn Pydantic validation error list into one readable string."""
    parts = []
    for e in errors[:5]:
        loc = e.get("loc", [])
        msg = e.get("msg", str(e))
        if isinstance(loc, (list, tuple)) and len(loc) > 1:
            field = loc[-1]
            parts.append(f"{field}: {msg}")
        else:
            parts.append(msg)
    return " ".join(parts) if parts else "Validation error"


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors() if hasattr(exc, "errors") else []
    logger.warning("Request validation failed: %s", errors)
    detail = _format_validation_detail(errors)
    return JSONResponse(status_code=422, content={"detail": detail})


@app.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(_request: Request, exc: ResponseValidationError) -> JSONResponse:
    errors = exc.errors() if hasattr(exc, "errors") else []
    logger.warning("Response validation failed: %s", errors)
    detail = _format_validation_detail(errors)
    return JSONResponse(status_code=500, content={"detail": f"Response error: {detail}"})


@app.get("/")
def root() -> dict[str, str]:
    """Root route so visiting the API URL doesn't 404."""
    return {
        "message": "NutriBot API",
        "docs": "/docs",
        "health": "/health",
        "api": "/api",
    }


@app.get("/health")
def health() -> dict[str, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok"}


app.include_router(api_router, prefix="/api")
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
