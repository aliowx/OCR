import logging
from contextlib import asynccontextmanager

from asgi_logger import AccessLoggerMiddleware
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware
from app.core.middleware.get_accept_language_middleware import (
    GetAcceptLanguageMiddleware,
)


from app.api.route import api_router
from app.api.docs import set_docs_routes
from app.core.config import ACCESS_LOG_FORMAT, STATIC_DIR, settings
from app.exceptions import exception_handlers
from app.models import User
from cache import Cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_cache = Cache()
    await redis_cache.init(
        host_url=str(settings.REDIS_URI),
        prefix=settings.store_prefix + "api-cache",
        response_header="X-API-Cache",
        ignore_arg_types=[Request, Response, Session, AsyncSession, User],
    )
    yield


openapi_url = f"{settings.API_V1_STR}/openapi.json"
if settings.SUB_PATH:
    openapi_url = f"/{settings.SUB_PATH}{openapi_url}"

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=openapi_url,
    redoc_url=None,
    docs_url=None,
    lifespan=lifespan,
    exception_handlers=exception_handlers,
)

logging.getLogger("uvicorn.access").handlers = []
AccessLoggerMiddleware.DEFAULT_FORMAT = ACCESS_LOG_FORMAT
app.add_middleware(AccessLoggerMiddleware)

static_route = "/static"
if settings.SUB_PATH:
    app.mount(f"/{settings.SUB_PATH}", app)
    static_route = f"/{settings.SUB_PATH}{static_route}"
    app.servers.append({"url": f"/{settings.SUB_PATH}"})

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
set_docs_routes(app, static_route)
app.add_middleware(GetAcceptLanguageMiddleware)
