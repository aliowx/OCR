import logging
import traceback
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import Response

from app import utils
from app.core.config import settings

logger = logging.getLogger(__name__)


class InternalServiceError(HTTPException):
    """Error class for failed internal services"""

    def __init__(
        self,
        message=None,
        msg_code=utils.MessageCodes.internal_error,
        msg_status=utils.MessageStatus.FAILURE,
        **kwargs,
    ) -> None:
        if not kwargs.get("status_code"):
            kwargs["status_code"] = 500
        if "detail" in kwargs:
            message = kwargs.pop("detail")
        super().__init__(detail=message, **kwargs)
        self.msg_code = msg_code
        self.msg_status = msg_status


class ServiceFailure(InternalServiceError):
    """
    Error class for failure in services
    use this for business logic erros
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        kwargs["status_code"] = 200
        kwargs["msg_status"] = utils.MessageStatus.FAILURE
        super().__init__(*args, **kwargs)


def get_traceback_info(exc: Exception):
    traceback_str = (traceback.format_tb(exc.__traceback__))[-1]
    traceback_full = "".join(traceback.format_tb(exc.__traceback__))
    exception_type = type(exc).__name__
    return exception_type, traceback_str, traceback_full


async def internal_service_exceptions_handler(request: Request, exc: Any):
    exception_type, traceback_str, traceback_full = get_traceback_info(exc)
    logger.error(f"Internal service error{exception_type}:\n{traceback_str}")

    response = utils.APIErrorResponse(
        data=str(exc.detail),
        msg_code=exc.msg_code,
        msg_status=exc.msg_status,
        status_code=exc.status_code,
    )
    return response


async def internal_exceptions_handler(request: Request, exc: Any):
    exception_type, traceback_str, traceback_full = get_traceback_info(exc)
    logger.error(
        f"Unhandled {exception_type} Exception Happened:\n{traceback_str}"
    )

    error_msg = ""
    if settings.DEBUG:
        error_msg = str(exc)

    return utils.APIErrorResponse(
        data=error_msg,
        msg_code=utils.MessageCodes.internal_error,
        msg_status=utils.MessageStatus.FAILURE,
        status_code=500,
    )


async def http_exception_handler(request: Request, exc: Any):
    if "WWW-Authenticate" in exc.headers:
        return Response(status_code=exc.status_code, headers=exc.headers)

    _, _, traceback_full = get_traceback_info(exc)

    response = utils.APIErrorResponse(
        data=exc.detail,
        msg_code=utils.MessageCodes.internal_error,
        msg_status=utils.MessageStatus.FAILURE,
        status_code=exc.status_code,
    )
    return response


async def validation_exceptions_handler(request: Request, exc: Any):
    exception_type, traceback_str, traceback_full = get_traceback_info(exc)

    response = utils.APIErrorResponse(
        data=exc.errors(),
        msg_code=utils.MessageCodes.input_error,
        msg_status=utils.MessageStatus.FAILURE,
        status_code=status.HTTP_400_BAD_REQUEST,
    )
    return response


async def response_validation_exceptions_handler(request: Request, exc: Any):
    exception_type, traceback_str, traceback_full = get_traceback_info(exc)
    logger.error(
        "Internal service response validation error:\n{}".format(exc.errors())
    )

    response = utils.APIErrorResponse(
        data="",
        msg_code=utils.MessageCodes.internal_error,
        msg_status=2,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    return response


exception_handlers = {
    HTTPException: http_exception_handler,
    Exception: internal_exceptions_handler,
    InternalServiceError: internal_service_exceptions_handler,
    RequestValidationError: validation_exceptions_handler,
    ResponseValidationError: response_validation_exceptions_handler,
}
