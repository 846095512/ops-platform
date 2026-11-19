import sys
from loguru import logger
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import pool, URL, text, create_engine, Engine, CursorResult

from src.core.config import get_settings, Settings


def ensure_database_exists() -> None:
    """
    严格校验 DATABASE_URL，返回 make_url 解析后的 URL 对象。
    校验项：
      1. 能被 SQLAlchemy 解析（语法合法）
      2. 后端为 MySQL
      3. 驱动在允许集合内
      4. host / username / database 必填
    任一不满足即抛 RuntimeError
    """
    example: str = "mysql+asyncmy://user:pass@host:3306/dbname?charset=utf8mb4"
    settings: Settings = get_settings()
    db_url: str = settings.database_url
    db_charset: str = settings.database_charset
    db_collation: str = settings.database_collation
    from sqlalchemy.engine.url import make_url
    from urllib.parse import quote
    try:
        pasted_db_url: str = db_url.replace("+asyncmy", "+pymysql").replace("+aiomysql", "+pymysql")
        quote(pasted_db_url, safe='')
        pasted_url: URL = make_url(pasted_db_url)
        db_name: str | None = pasted_url.database
    except Exception as err:
        raise RuntimeError(
            f"  DATABASE_URL is not invalid, can not resolve: \n"
            f"  Original value: {db_url!r}\n"
            f"  resolve error: {err}\n"
            f"  plz check .env key  DATABASE_URL\n"
            f"  example: mysql+asyncmy://user:pass@host:3306/dbname"
        )

    missing = [
        name
        for name, val in (
            ("host", pasted_url.host),
            ("username", pasted_url.username),
            ("database", pasted_url.database))
        if not val
    ]

    if missing:
        raise RuntimeError(
            f"\n DATABASE_URL Missing required field: {', '.join(missing)}\n"
            f"   Current value: {pasted_url.render_as_string(hide_password=True)}\n"
            f"   example: {example}"
        )
    admin_url: URL = pasted_url.set(database="mysql")

    engine: Engine = create_engine(
        admin_url,
        poolclass=pool.NullPool,
        isolation_level="AUTOCOMMIT",  # DDL 需 AUTOCOMMIT
    )
    try:
        with engine.connect() as conn:
            result: CursorResult = conn.execute(
                text(
                    "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
                    "WHERE SCHEMA_NAME = :name"
                ),
                {"name": db_name})
            exists: bool = result.first() is not None
            if exists:
                logger.info(f"Database `{db_name}` already exists,Skip creation......")
                return
            conn.execute(
                text(
                    f"CREATE DATABASE `{db_name}`"
                    f"CHARACTER SET `{db_charset}` COLLATE `{db_collation}`"
                ))
            logger.info(f"数据库 `{db_name}` created......")
    finally:
        engine.dispose()


def run_migrations():
    ensure_database_exists()

    alembic_cfg_path: Path = Path(__file__).parent.parent / "alembic.ini"
    alembic_cfg: Config = Config(str(alembic_cfg_path))
    sql_output_dir: Path = Path(get_settings().migration_dir).resolve()
    sql_output_dir.mkdir(parents=True, exist_ok=True)

    if not alembic_cfg_path.exists():
        raise FileNotFoundError(f"alembic.ini not found: {alembic_cfg_path}")

    # 1. 动态注入数据库连接串（防止 alembic.ini 中写死或为空）
    settings: Settings = get_settings()
    sync_db_url: str = settings.database_url.replace("+asyncmy", "+pymysql").replace("+aiomysql", "+pymysql")
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
