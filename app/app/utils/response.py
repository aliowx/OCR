from enum import IntEnum
from typing import Any, Generic, TypeVar

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app import utils

T = TypeVar("T")


class MessageStatus(IntEnum):
    SUCCESS = 0
    FAILURE = 1


class ApiResponseHeader(BaseModel, Generic[T]):
    """Header type of APIResponseType"""

    status: int = 0
    message: str = "Successful Operation"
    persianMessage: str = "عملیات موفق"
    messageCode: int = Field(
        ..., description=str(utils.MessageCodes.messages_names)
    )


class PaginatedContent(BaseModel, Generic[T]):
    """Content data type for lists with pagination"""

    data: T
    total_count: int = 0
    size: int | None = None
    page: int = 1


class APIResponseType(BaseModel, Generic[T]):
    """
    an api response type for using as the api's router response_model
    use this for apis that use our APIResponse class for their output
    """

    header: ApiResponseHeader
    content: T | None = None


class APIResponse:
    """
    Custom reponse class for apis
    Adds custom header, messages to reponses
    """

    header: ApiResponseHeader
    content: Any = None

    def __init__(
        self,
        data: Any,
        *args,
        msg_code: int = 0,
        msg_status: MessageStatus = MessageStatus.SUCCESS,
        **kwargs
    ) -> None:
        self.header = ApiResponseHeader(
            status=msg_status,
            message=utils.MessageCodes.messages_names[msg_code],
            persianMessage=utils.MessageCodes.persian_message_names[msg_code],
            messageCode=msg_code,
        )
        if isinstance(data, BaseModel):
            self.content = data.model_dump()
        else:
            self.content = jsonable_encoder(data)


class APIErrorResponse(JSONResponse):
    """
    Custom error reponse class for apis
    Adds custom header, messages to error reponses
    """

    def __init__(
        self,
        data: Any,
        msg_code: int = utils.MessageCodes.successful_operation,
        msg_status: MessageStatus = MessageStatus.FAILURE,
        header: dict | None = None,
        **kwargs
    ) -> None:
        header_data = {
            "status": msg_status,
            "message": utils.MessageCodes.messages_names[msg_code],
            "persianMessage": utils.MessageCodes.persian_message_names[
                msg_code
            ],
            "messageCode": msg_code,
        }
        if header:
            header_data = header
        self.response_data = {
            "header": header_data,
            "content": jsonable_encoder(data),
        }
        super().__init__(self.response_data, **kwargs)
