import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.app.api.artifacts import router as artifacts_router
from backend.app.api.chat import router as chat_router
from backend.app.api.sessions import router as sessions_router
from backend.app.config import get_settings
from backend.app.database import AsyncSessionLocal


settings = get_settings()


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=getattr(
        logging,
        settings.log_level.upper(),
        logging.INFO,
    ),
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)

logger = logging.getLogger("lenny_growth_assistant")


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Lenny Growth Assistant",
    description="RAG-powered assistant for Lenny's Podcast knowledge",
    version="0.1.0",
)


# ============================================================
# CORS
# ============================================================

# Frontend development origin.
# We will make this configurable later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST ID + REQUEST LOGGING
# ============================================================

@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    logger.info(
        "request_started request_id=%s method=%s path=%s",
        request_id,
        request.method,
        request.url.path,
    )

    try:
        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request_completed request_id=%s method=%s path=%s status=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
        )

        return response

    except Exception:
        logger.exception(
            "request_failed request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )
        raise


# ============================================================
# GLOBAL UNEXPECTED ERROR HANDLER
# ============================================================

@app.exception_handler(Exception)
async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
):
    request_id = getattr(
        request.state,
        "request_id",
        "unknown",
    )

    logger.exception(
        "unhandled_exception request_id=%s method=%s path=%s error_type=%s",
        request_id,
        request.method,
        request.url.path,
        type(exc).__name__,
    )

    return JSONResponse(
        status_code=500,
        headers={
            "X-Request-ID": request_id,
        },
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred.",
            "request_id": request_id,
        },
    )


# ============================================================
# ROUTERS
# ============================================================

app.include_router(chat_router)
app.include_router(sessions_router)
app.include_router(artifacts_router)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():
    return {
        "name": "Lenny Growth Assistant",
        "status": "running",
        "version": "0.1.0",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
async def health():
    """
    Operational health endpoint.

    Checks the application's critical dependencies without
    exposing secrets such as API keys.
    """

    database_status = "healthy"

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        logger.exception("database_health_check_failed")
        database_status = "unavailable"

    ollama_status = "healthy"

    try:
        import httpx

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=2.0,
                read=5.0,
                write=5.0,
                pool=5.0,
            )
        ) as client:
            response = await client.get(
                f"{settings.ollama_base_url.rstrip('/')}/api/tags"
            )
            response.raise_for_status()

    except Exception:
        logger.exception("ollama_health_check_failed")
        ollama_status = "unavailable"

    provider = settings.default_llm_provider.lower()

    anthropic_status = (
        "configured"
        if settings.anthropic_api_key.strip()
        else "not_configured"
    )

    overall_status = (
        "healthy"
        if database_status == "healthy"
        and (
            provider != "ollama"
            or ollama_status == "healthy"
        )
        else "degraded"
    )

    return {
        "status": overall_status,
        "database": database_status,
        "ollama": ollama_status,
        "vector_index": "configured",
        "llm_provider": provider,
        "anthropic": anthropic_status,
    }