from alembic import context
from alembic.config import Config
from sqlalchemy import pool, MetaData
from sqlmodel import SQLModel

from src.core.config import get_settings, Settings

config: Config = context.config
target_metadata: MetaData = SQLModel.metadata

settings: Settings = get_settings()
db_url: str = settings.database_url or ""

if not db_url:
    raise RuntimeError(f" database url is not defined......")

sync_db_url: str = db_url.replace("+asyncmy", "+pymysql").replace("+aiomysql", "+pymysql")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=sync_db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    from sqlalchemy import create_engine
    connectable = create_engine(
        sync_db_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
