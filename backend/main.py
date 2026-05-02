"""
AdTicks — FastAPI application entry point.

Mounts all routers under the /api prefix, configures CORS, and registers
a lifespan event that creates all database tables on startup.
"""

import time
import uuid
from contextlib import asynccontextmanager

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api import (
    auth, projects, seo, ai, gsc, ads, insights, scores, aeo, seo_suite, geo,
    progress, cache, clusters, seo_competitive
)
from app.api import seo_meta_tags, seo_content_analysis, seo_technical, seo_advanced, seo_extra
from app.core.config import settings
from app.core.database import Base, engine
from app.core.exceptions import AdTicksException
from app.core.logging import get_logger, set_request_id, setup_logging
from app.core.caching import get_redis_client, close_redis_client

logger = get_logger(__name__)
limiter = Limiter(key_func=get_remote_address)


# Initialize Sentry for error tracking
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions
        environment=settings.ENVIRONMENT,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all tables and storage folders when the application starts."""
    # Setup logging
    setup_logging(settings.ENVIRONMENT)
    logger.info("application_startup", extra={"environment": settings.ENVIRONMENT})
    
    # Ensure storage root exists
    import os
    os.makedirs(settings.STORAGE_ROOT, exist_ok=True)
    logger.info("storage_initialized", extra={"path": settings.STORAGE_ROOT})

    # Import models so metadata is populated before create_all
    import app.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("database_ready")
    
    # Initialize Redis client
    redis_client = await get_redis_client()
    if redis_client:
        logger.info("redis_initialized")
    
    yield
    
    # Graceful shutdown
    logger.info("application_shutdown")
    
    # Close AEO services
    try:
        from app.api.aeo import visibility_service
        await visibility_service.close()
    except Exception as e:
        logger.warning(f"failed_to_close_visibility_service: {e}")
        
    await close_redis_client()
    await engine.dispose()


app = FastAPI(
    title="AdTicks — Visibility Intelligence Platform",
    description="Backend API for the AdTicks AI visibility platform.",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
if settings.ENVIRONMENT == "development":
    origins = ["*"]
else:
    # Production: include the public domain and localhost for docker compose
    origins = settings.ALLOWED_ORIGINS
    # Ensure production domain is always included
    if "https://adticks.com" not in origins:
        origins.append("https://adticks.com")
    # Always allow the app's own domain for avatar/storage requests
    if settings.BASE_URL not in origins:
        origins.append(settings.BASE_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request ID Tracking Middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to each request for tracing."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    set_request_id(request_id)
    
    # Set Sentry context
    sentry_sdk.set_context(
        "request",
        {"id": request_id, "path": request.url.path, "method": request.method}
    )
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ---------------------------------------------------------------------------
# Request Logging Middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses."""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "http_request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
    except Exception as exc:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "http_request_failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
                "error": str(exc),
            },
        )
        raise


# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers and suppress Privacy Sandbox console errors."""
    response = await call_next(request)
    # Explicitly disable Privacy Sandbox features to stop browser "Unrecognized feature" errors
    # and provide standard security hardening.
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), "
        "browsing-topics=(), join-ad-interest-group=(), "
        "run-ad-auction=(), attribution-reporting=(), "
        "private-state-token-issuance=(), private-state-token-redemption=()"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------
@app.exception_handler(AdTicksException)
async def adticks_exception_handler(request: Request, exc: AdTicksException):
    """Handle custom AdTicks exceptions."""
    logger.warning(
        "application_exception",
        extra={
            "code": exc.code,
            "message": exc.message,
            "status_code": exc.status_code,
            "details": exc.details,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.code,
            "message": exc.message,
            "detail": exc.message,  # Added for frontend compatibility
            "details": exc.details,
        },
    )


from fastapi.exceptions import HTTPException as FastAPIHTTPException

@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    """Handle standard FastAPI HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "detail": exc.detail,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(
        "unhandled_exception",
        extra={
            "error_type": type(exc).__name__,
            "error": str(exc),
        },
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded."""
    logger.warning(
        "rate_limit_exceeded",
        extra={
            "path": request.url.path,
            "limit": exc.detail,
        },
    )
    return JSONResponse(
        status_code=429,
        content={
            "error": "RATE_LIMIT_EXCEEDED",
            "message": "Too many requests. Please try again later.",
        },
    )

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
API_PREFIX = "/api"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(projects.router, prefix=API_PREFIX)
app.include_router(seo.router, prefix=API_PREFIX)
app.include_router(seo_suite.router, prefix=API_PREFIX)
app.include_router(seo_meta_tags.router, prefix=API_PREFIX)
app.include_router(seo_content_analysis.router, prefix=API_PREFIX)
app.include_router(seo_technical.router, prefix=API_PREFIX)
app.include_router(seo_advanced.router, prefix=API_PREFIX)
app.include_router(seo_extra.router, prefix=API_PREFIX)
app.include_router(ai.router, prefix=API_PREFIX)
app.include_router(aeo.router, prefix=API_PREFIX)
app.include_router(gsc.router, prefix=API_PREFIX)
app.include_router(ads.router, prefix=API_PREFIX)
app.include_router(insights.router, prefix=API_PREFIX)
app.include_router(scores.router, prefix=API_PREFIX)
app.include_router(geo.router, prefix=API_PREFIX)
app.include_router(clusters.router, prefix=API_PREFIX)
app.include_router(progress.router, prefix=API_PREFIX)
app.include_router(cache.router, prefix=API_PREFIX)
app.include_router(seo_competitive.router, prefix=API_PREFIX)


# ---------------------------------------------------------------------------
# Static Files (Storage)
# ---------------------------------------------------------------------------
# Mount the storage directory so uploaded files (avatars, etc.) are public
app.mount(f"{API_PREFIX}/storage", StaticFiles(directory=settings.STORAGE_ROOT), name="storage")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["health"])
async def health_check():
    """Return service health status."""
    return {"status": "ok", "environment": settings.ENVIRONMENT}
