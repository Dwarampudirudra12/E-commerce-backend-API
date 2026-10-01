"""FastAPI entrypoint — Milestone 1: auth + RBAC + health + versioned API + Swagger."""
import time
import uuid

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.routers import auth, health, users

settings = get_settings()
structlog.configure(processors=[structlog.processors.JSONRenderer()])

app = FastAPI(
    title="E-Commerce Backend API",
    version="0.1.0-m1",
    description=(
        "M1: Project init, design + core setup. JWT auth + RBAC for 4 roles, "
        "versioned API (/api/v1), health checks, OpenAPI docs."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # M4: restrict to frontend domains + Nginx TLS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_logging(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.time()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    structlog.get_logger().info(
        "request", request_id=request_id, route=request.url.path,
        status=response.status_code, duration_ms=int((time.time() - start) * 1000))
    return response


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": "http_error",
                 "request_id": request.headers.get("X-Request-ID")},
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc.errors()), "code": "validation_error"},
    )


# Versioned API (doc 1.3: /api/v1 single source of truth).
app.include_router(health.router)  # unversioned: /health/live, /health/ready
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)


@app.get("/", include_in_schema=False)
def root():
    return {"name": settings.APP_NAME, "version": app.version,
            "docs": "/docs", "health": "/health/live"}
