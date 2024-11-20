import enum
import logging
import secrets
from pathlib import Path
from typing import Optional

from pydantic import (
    AnyHttpUrl,
    Extra,
    PostgresDsn,
    RedisDsn,
    field_validator,
    HttpUrl,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

import app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s|%(levelname)s|%(name)s|%(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
logging.getLogger("httpx").propagate = False
logging.getLogger("cache.client").propagate = False
ACCESS_LOG_FORMAT = "%(h)s|%(H)s|%(m)s|%(U)s|%(s)s|%(M)s|%(a)s"

BASE_DIR = Path(app.__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


class AuthMethod(str, enum.Enum):
    BASIC = "basic"
    JWT = "jwt"


class SettingsBase(BaseSettings):
    PROJECT_NAME: str
    API_V1_STR: str = "/api/v1"
    SUB_PATH: str | None = None
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str
    DEBUG: bool = False
    TZ: str = "Asia/Tehran"
    PGTZ: str = "Asia/Tehran"

    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 1 day = 1 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 1
    ALLOWED_AUTH_METHODS: list[AuthMethod] | str = [AuthMethod.JWT]

    @field_validator("SUB_PATH", mode="before")
    @classmethod
    def strip_subpath(cls, v: str | None) -> str:
        if v is not None:
            return v.strip("/")

    @field_validator("ALLOWED_AUTH_METHODS", mode="before")
    @classmethod
    def assemble_allowed_auth_methods(
        cls, v: str | list[str]
    ) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] | str = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str):
            return [i.strip() for i in v.strip("[]").split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @property
    def allow_origins(self) -> list[str]:
        return [str(origin).strip("/") for origin in self.BACKEND_CORS_ORIGINS]

    @property
    def store_prefix(self) -> str:
        return self.PROJECT_NAME.lower().replace(" ", "-") + "-"

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


class StorageSettings(SettingsBase):
    REDIS_TIMEOUT: int | None = 5
    REDIS_URI: RedisDsn | None = None

    AUTO_GEN_EVENT_FAKE: int | None = None
    DATA_FAKE_SET: bool | None = False

    CHECKING_FREE_TIME_BETWEEN_RECORDS_ENTRANCEDOOR_EXITDOOR: int | None = None
    FREE_TIME_BETWEEN_RECORDS_ENTRANCEDOOR_EXITDOOR: int | None = None

    CLEANUP_COUNT: Optional[int] = 1000  # cleanup 1000 images
    CLEANUP_PERIOD: Optional[int] = 30  # every 30 seconds
    CLEANUP_AGE: Optional[float] = 2.5  # which are older than 2.5 days
    CLEANUP_EVENTS_AGE: Optional[float] = (
        30.5  # which are older than 30.5 days
    )
    CLEANUP_RECORDS_AGE: Optional[float] = (
        90.5  # which are older than 30.5 days
    )

    SQLALCHEMY_DATABASE_URI: PostgresDsn | None = None
    SQLALCHEMY_POOL_SIZE: int = 15
    SQLALCHEMY_POOL_TIMEOUT: int = 30
    SQLALCHEMY_POOL_RECYCLE: int = 3600
    SQLALCHEMY_MAX_OVERFLOW: int = 5

    URL_FOR_SET_DATA_FAKE: str = None

    # database test
    TEST_SQLALCHEMY_DATABASE_URI: PostgresDsn | None = None
    # dsn database test
    TEST_DSN_POSTGRES_NAME: str = None
    TEST_DSN_POSTGRES_PASSWORD: str = None
    TEST_DSN_POSTGRES_IP: str = None
    TEST_DSN_POSTGRES_PORT: str = None
    TEST_DSN_POSTGRES_DB_NAME: str = None

    TEST_FIRST_SUPERUSER: str = None
    TEST_FIRST_SUPERUSER_PASSWORD: str = None

    # payment
    PAYMENT_ADDRESS: HttpUrl
    PAYMENT_USER_NAME: str
    PAYMENT_PASSWORD: str
    PAYMENT_REQUEST_VERIFY_SSL: bool

    # pay
    GATEWAY_TYPE_PAY: str = None
    PROVIDER_PAY: str = None
    TERMINAL_PAY: str = None
    USER_NAME_PAY: str = None
    PASSWORD_USER_PAY: str = None
    CALL_BACK_PAY: str = HttpUrl

    # sms
    URL_SEND_SMS: str = None

    # MinIO
    MINIO_URL: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool
    MINIO_BUCKET_NAME: str

    @property
    def async_database_url(self) -> str | None:
        return (
            str(self.SQLALCHEMY_DATABASE_URI).replace(
                "postgresql://", "postgresql+asyncpg://"
            )
            if self.SQLALCHEMY_DATABASE_URI
            else self.SQLALCHEMY_DATABASE_URI
        )


settings = StorageSettings()
