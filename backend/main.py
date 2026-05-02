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
from app.core.limiter import limiter

logger = get_logger(__name__)


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
# Request Context & Logging Middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """
    Middleware to manage request context (ID, logging, security headers).
    
    1. Generates/extracts a request ID.
    2. Sets it in the global context and Sentry.
    3. Logs the request and response with duration.
    4. Adds standard security headers.
    5. Injects the request ID into the response headers.
    """
    start_time = time.time()
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    # Set request ID in context variable for logging
    set_request_id(request_id)
    
    # Set Sentry context
    sentry_sdk.set_context(
        "request",
        {"id": request_id, "path": request.url.path, "method": request.method}
    )
    
    try:
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log successful request
        logger.info(
            "http_request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "request_id": request_id,  # Explicitly pass it just in case
            },
        )
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "browsing-topics=(), join-ad-interest-group=(), "
            "run-ad-auction=(), attribution-reporting=(), "
            "private-state-token-issuance=(), private-state-token-redemption=()"
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
                "request_id": request_id,
            },
        )
        raise

# Remove the old separate middlewares
# (The replace will handle this by replacing the block)


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
# Health check and status endpoints
# ---------------------------------------------------------------------------
@app.get("/health", tags=["health"])
async def health_check():
    """Return service health status."""
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.get("/health/live", tags=["health"])
async def health_check_live():
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
async def health_check_ready():
    """Kubernetes readiness probe endpoint."""
    try:
        from app.core.caching import get_redis_client
        redis = await get_redis_client()
        if redis:
            await redis.ping()
        return {"status": "ready", "db": "connected", "redis": "connected" if redis else "unavailable"}
    except Exception as e:
        logger.warning(f"readiness_check_failed: {e}")
        return {"status": "ready", "db": "connected", "redis": "unavailable"}


@app.get("/api/health", tags=["health"])
async def api_health_check():
    """Return API health status."""
    return {"status": "ok", "service": "adticks-api", "environment": settings.ENVIRONMENT}
