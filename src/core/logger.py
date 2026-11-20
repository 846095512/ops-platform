import inspect
import logging
import sys
from contextvars import ContextVar
from functools import lru_cache
from pathlib import Path

from loguru import logger

from src.core.config import get_settings, Settings

settings: Settings = get_settings()

# 异步安全的请求上下文；未进入请求时默认 "-"
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class InterceptHandler(logging.Handler):
    """把标准库 logging 记录转发给 Loguru，并保持真实的调用来源。"""

    def emit(self, record: logging.LogRecord) -> None:
        # 1. 级别映射
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 2. 从当前帧向上跳过所有 logging 模块内部帧，找到真正的调用方
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        # 3. 用 opt(depth=...) 让 Loguru 从正确栈深度推断 name/function/line
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


@lru_cache
def setup_logging() -> None:
    # 先移除默认 handler，避免重复输出
    logger.remove()

    # 统一注入 request_id（每条日志生成时动态读取 ContextVar）
    logger.configure(
        extra={"request_id": "-"},
        patcher=lambda record: record["extra"].update(
            request_id=request_id_var.get()
        ),
    )

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    rotation = (
        settings.log_when
        if settings.log_rotate_type == "time"
        else settings.log_max_size
    )

    common_config = {
        "format": settings.log_format,
        "enqueue": True,
        "backtrace": True,
        "diagnose": False,  # 生产建议 False，避免泄露变量值
    }

    file_config = {
        **common_config,
        "rotation": rotation,
        "retention": settings.log_backup_count,
        "compression": "zip",
        "encoding": settings.log_encoding,
    }

    # 1. 控制台
    logger.add(
        sys.stdout,
        level=settings.log_level_console,
        colorize=True,
        **common_config,
    )

    # 2. 业务日志文件：只收 ERROR 以下（DEBUG/INFO/WARNING 等）
    logger.add(
        log_dir / "app.log",
        level=settings.log_level_app,
        filter=lambda r: r["level"].no < logging.ERROR,
        **file_config,
    )

    # 3. 错误日志文件：只收 ERROR 及以上
    logger.add(
        log_dir / "error.log",
        level=settings.log_level_error,
        filter=lambda r: r["level"].no >= logging.ERROR,
        **file_config,
    )

    # 4. 接管标准库 logging（uvicorn / sqlalchemy / alembic 等）
    logging.basicConfig(
        handlers=[InterceptHandler()],
        level=settings.log_level_app,
        force=True,
    )

    # 根 logger 兜底
    root_logger = logging.getLogger()
    root_logger.handlers = [InterceptHandler()]
    root_logger.setLevel(settings.log_level_app)

    # 框架 logger 单独接管并切断传播，避免重复
    known_loggers = [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
        "sqlalchemy",
        "sqlalchemy.engine",
        "alembic",
        "gunicorn",
    ]
    for name in known_loggers:
        lib_logger = logging.getLogger(name)
        lib_logger.handlers = [InterceptHandler()]
        lib_logger.propagate = False
