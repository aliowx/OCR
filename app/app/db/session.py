from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from app.core.config import settings

engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    pool_pre_ping=True,
    max_overflow=settings.SQLALCHEMY_MAX_OVERFLOW,
    pool_size=settings.SQLALCHEMY_POOL_SIZE,
    pool_timeout=settings.SQLALCHEMY_POOL_TIMEOUT,
    pool_recycle=settings.SQLALCHEMY_POOL_RECYCLE,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async_engine = create_async_engine(
    settings.async_database_url,
    pool_pre_ping=True,
    max_overflow=settings.SQLALCHEMY_MAX_OVERFLOW,
    pool_size=settings.SQLALCHEMY_POOL_SIZE,
    pool_timeout=settings.SQLALCHEMY_POOL_TIMEOUT,
    pool_recycle=settings.SQLALCHEMY_POOL_RECYCLE,
)
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# for celery usage
ScopedSession = scoped_session(SessionLocal)
