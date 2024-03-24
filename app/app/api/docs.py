from fastapi import APIRouter, Depends, FastAPI
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.openapi.utils import get_openapi

from app.api.deps import basic_auth_superuser
from app.core.config import settings


def set_docs_routes(app: FastAPI, static_route: str) -> None:
    router = APIRouter()

    swagger_ui_oauth2_redirect_url = app.swagger_ui_oauth2_redirect_url
    if not swagger_ui_oauth2_redirect_url:
        swagger_ui_oauth2_redirect_url = "/docs/oauth2-redirect"

    @router.get(swagger_ui_oauth2_redirect_url, include_in_schema=False)
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    @router.get(
        "/docs",
        include_in_schema=False,
        dependencies=[Depends(basic_auth_superuser)],
    )
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url=f"{static_route}/swagger-ui-bundle.js",
            swagger_css_url=f"{static_route}/swagger-ui.css",
        )

    @router.get(
        "/redoc",
        include_in_schema=False,
        dependencies=[Depends(basic_auth_superuser)],
    )
    async def redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=app.title + " - ReDoc",
            redoc_js_url=f"{static_route}/redoc.standalone.js",
        )

    @router.get(
        "/openapi.json",
        include_in_schema=False,
        dependencies=[Depends(basic_auth_superuser)],
    )
    async def openapi():
        return get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
            servers=[{"url": settings.SUB_PATH if settings.SUB_PATH else ""}],
        )

    app.include_router(router)
