from functools import lru_cache
from typing import Any, AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine

from src.core.config import get_settings, Settings


@lru_cache
def get_engine() -> AsyncEngine:
    """全局单例引擎，第一次调用时创建，之后直接取缓存"""
    settings: Settings = get_settings()
    return create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        echo=False,
    )


@lru_cache
def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """全局单例 Session 工厂"""
    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """供 FastAPI 注入"""
    session_maker: async_sessionmaker[AsyncSession] = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
