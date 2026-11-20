import sys
from pathlib import Path
from urllib.parse import urlparse

from alembic import command
from alembic.config import Config
from loguru import logger
from sqlalchemy import pool, text, create_engine, Engine

from src.core.config import get_settings, Settings

settings: Settings = get_settings()


def get_sync_db_url() -> str:
    db_url: str | None = settings.database_url
    if db_url is None:
        raise RuntimeError(f"Database url not found: {db_url}")
    return db_url.replace("+asyncmy", "+pymysql").replace("+aiomysql", "+pymysql")


def _create_database_if_not_exists() -> None:
    """
        将异步连接库替换为同步库,执行SQL升级时,同步执行
        并确保创建ops库
    """
    database_url = ""
    engine: Engine | None = None
    try:
        parsed = urlparse(get_sync_db_url())
        database_name = parsed.path.lstrip("/")
        database_url = f"{parsed.scheme}://{parsed.netloc}"
        engine: Engine = create_engine(
            database_url,
            poolclass=pool.NullPool,
            isolation_level="AUTOCOMMIT",  # DDL 需 AUTOCOMMIT
        )
        with engine.connect() as conn:
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{database_name}`"
                    f"CHARACTER SET `{settings.database_charset}`"
                ))
    except Exception as err:
        raise RuntimeError(f"Failed to create database: {err}, current_database_url: {database_url}")
    finally:
        if engine is not None:
            engine.dispose()


def run_migrations():
    _create_database_if_not_exists()

    alembic_cfg_path: Path = Path(__file__).parent.parent / "alembic.ini"
    alembic_cfg: Config = Config(str(alembic_cfg_path))
    sql_output_dir: Path = Path(get_settings().migration_dir).resolve()
    sql_output_dir.mkdir(parents=True, exist_ok=True)

    if not alembic_cfg_path.exists():
        raise FileNotFoundError(f"alembic.ini not found: {alembic_cfg_path}")

    # 1. 动态注入数据库连接串（防止 alembic.ini 中写死或为空）
    sync_db_url = get_sync_db_url()
    alembic_cfg.set_main_option("sqlalchemy.url", sync_db_url)
    sql_file_path: Path = Path(sql_output_dir) / "upgrade.sql"

    # 2. 生成 SQL（离线）
    logger.info("Start generating database upgrade SQL file...")
    original_stdout = sys.stdout
    try:
        with open(sql_file_path, "w", encoding="utf-8") as f:
            sys.stdout = f
            command.upgrade(alembic_cfg, "head", sql=True)
    except Exception as err:
        raise RuntimeError(f"Failed to generate SQL: {err}")
    finally:
        sys.stdout = original_stdout
    logger.info("End generating database upgrade SQL file...")

    # 3. 在线升级
    try:
        logger.info("Start executing the database upgrade...")
        command.upgrade(alembic_cfg, "head")
        logger.info("End executing the database upgrade...")
    except Exception as err:
        logger.exception("Database upgrade failed")
        raise RuntimeError(f"Failed to execute upgrade: {err}")
