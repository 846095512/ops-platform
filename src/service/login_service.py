from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlmodel import col

from src.models.system import System
from src.core.tools import CURRENT_APP_ID


async def fetch_secret_key_from_db() -> str:
    """
    从数据库查询真正的 Secret Key。
    """
    from core.database import get_engine
    try:
        session_local = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        async with session_local() as session:
            result = await session.execute(select(System).where(col(System.id) == CURRENT_APP_ID))
            sk = result.scalar_one_or_none().secret_key

            print(sk)
        if not sk:
            logger.warning("Secret key not found in DB, using fallback.")
            raise RuntimeError("DB secret key not found in DB")
        return sk
    except Exception as e:
        logger.exception("Failed to fetch secret key from DB")
        raise RuntimeError(f"DB secret key retrieval error: {e}")
