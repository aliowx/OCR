from typing import Any, Callable

from fastapi import APIRouter as FastAPIRouter

from app.api.api_v1.endpoints import (
    users,
    utils,
)


class APIRouter(FastAPIRouter):
    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        include_in_schema: bool = True,
        **kwargs: Any
    ) -> None:
        if path.endswith("/"):
            alternate_path = path[:-1]
        else:
            alternate_path = path + "/"
        super().add_api_route(
            alternate_path, endpoint, include_in_schema=False, **kwargs
        )
        return super().add_api_route(
            path, endpoint, include_in_schema=include_in_schema, **kwargs
        )


api_router = APIRouter()
api_router.include_router(users.router, prefix="/user", tags=["users"])
api_router.include_router(utils.router, prefix="/util", tags=["utils"])

