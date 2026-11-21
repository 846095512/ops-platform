from contextlib import asynccontextmanager, AsyncExitStack
from pathlib import Path

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from filelock import FileLock, Timeout
from loguru import logger


@asynccontextmanager
async def lifespan_migration(_app: FastAPI):
    from src.core.migration import run_migrations
    """
    使用 filelock 实现跨平台文件锁。
    通过 set 检查，防止多个 worker 同时执行迁移导致冲突。
    """
    lock_file_path = Path(__file__).resolve().parent / "migration.lock"
    lock = FileLock(lock_file_path, timeout=60)
    try:
        with lock.acquire(timeout=0):
            logger.info("Migration lock acquired. Running database migrations...")
            await run_in_threadpool(run_migrations)
            logger.info("Database migrations completed.")
    except Timeout:
        logger.warning("Migration lock is held by another process. Skipping migrations.")
    except Exception as e:
        logger.exception(f"Unexpected error while acquiring lock or running migrations: {e}")
        raise e
    yield


@asynccontextmanager
async def lifespan_database(_app: FastAPI):
    yield
    from src.core.database import get_engine
    logger.info("Closing database connection pool...")
    await get_engine().dispose()
    logger.info("Database connection pool disposed.")


@asynccontextmanager
async def combined_lifespan(_app: FastAPI):
    try:
        async with AsyncExitStack() as stack:
            await stack.enter_async_context(lifespan_migration(_app))
            await stack.enter_async_context(lifespan_database(_app))
            yield
    except Exception as exc:
        logger.exception(exc)
        raise exc
