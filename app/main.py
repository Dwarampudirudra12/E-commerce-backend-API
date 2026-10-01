"""FastAPI entrypoint — Milestone 2: core commerce (catalog/cart/orders/payments)."""
import time
import uuid

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core import metrics as prom
from app.core.config import get_settings
from app.routers import auth, cart, catalog, forecast, health, notifications, orders, payments, recommend, reports, users

settings = get_settings()
structlog.configure(processors=[structlog.processors.JSONRenderer()])

app = FastAPI(
    title="E-Commerce Backend API",
    version="0.3.0-m3",
    description=(
        "M3: fraud tuning + review queue, demand forecasts, recommendations, "
        "notifications, analytics + dashboard APIs."
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
    duration = time.time() - start
    structlog.get_logger().info(
        "request", request_id=request_id, route=request.url.path,
        status=response.status_code, duration_ms=int(duration * 1000))
    route = request.url.path
    if not route.startswith("/metrics"):
        prom.HTTP_REQUESTS.labels(method=request.method, route=route,
                                  status=str(response.status_code)).inc()
        prom.HTTP_LATENCY.labels(route=route).observe(duration)
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
app.include_router(catalog.router, prefix=settings.API_V1_PREFIX)
app.include_router(catalog.cat_router, prefix=settings.API_V1_PREFIX)
app.include_router(cart.router, prefix=settings.API_V1_PREFIX)
app.include_router(orders.router, prefix=settings.API_V1_PREFIX)
app.include_router(payments.router, prefix=settings.API_V1_PREFIX)
app.include_router(reports.router, prefix=settings.API_V1_PREFIX)
app.include_router(forecast.router, prefix=settings.API_V1_PREFIX)
app.include_router(recommend.router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications.router, prefix=settings.API_V1_PREFIX)


@app.get("/metrics", include_in_schema=False)
def metrics():
    body, ctype = prom.exposition()
    return Response(content=body, media_type=ctype)


import os as _os
_os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/", include_in_schema=False)
def root():
    return {"name": settings.APP_NAME, "version": app.version,
            "docs": "/docs", "health": "/health/live"}
