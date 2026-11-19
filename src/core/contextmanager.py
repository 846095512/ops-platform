from loguru import logger
from contextlib import asynccontextmanager, AsyncExitStack
from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool

from src.core.security import security
from src.service.login_service import fetch_secret_key_from_db



@asynccontextmanager
async def lifespan_migration(_app: FastAPI):
    from src.core.migration import run_migrations
    # 将同步的阻塞代码放入线程池运行，防止阻塞主事件循环
    await run_in_threadpool(run_migrations)
    yield


@asynccontextmanager
async def lifespan_database(_app: FastAPI):
    yield
    from src.core.database import get_engine
    logger.info("Closing database connection pool...")
    await get_engine().dispose()
    logger.info("Database connection pool disposed.")


@asynccontextmanager
async def lifespan_get_secret_key(_app: FastAPI):
    sk = await fetch_secret_key_from_db()
    security.set_secret_key(sk)
    logger.info("Secret key loaded successfully!")
    yield
    security.clear()


@asynccontextmanager
async def combined_lifespan(_app: FastAPI):
    try:
        async with AsyncExitStack() as stack:

            await stack.enter_async_context(lifespan_migration(_app))

            await stack.enter_async_context(lifespan_database(_app))

            await stack.enter_async_context(lifespan_get_secret_key(_app))
            yield
    except Exception as exc:
        logger.exception(exc)
        raise exc
