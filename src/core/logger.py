import sys
import logging
from pathlib import Path
from loguru import logger
from src.core.config import get_settings, Settings

settings: Settings = get_settings()


class InterceptHandler(logging.Handler):
    """
    日志拦截器：直接提取标准库真实上下文
    """

    def emit(self, record: logging.LogRecord) -> None:
        # 1. 映射日志级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 2. 提取开发者通过 extra={} 传入的自定义字段
        # 通过对比标准 LogRecord 的默认属性，精准过滤出自定义字段
        default_attrs = logging.LogRecord("", 0, "", 0, "", None, None).__dict__.keys()
        extra_dict = {k: v for k, v in record.__dict__.items() if k not in default_attrs}

        # 3. 【核心杀招】使用 patch 强行注入真实的模块名、函数名、行号和文件路径
        # 这样 Loguru 在渲染 {name}, {function}, {line} 时，就会使用我们传入的真实值
        logger.patch(lambda log_record: log_record.update({
            "name": record.name,
            "function": record.funcName,
            "line": record.lineno,
            "extra": {**log_record["extra"], **extra_dict}
        })).opt(exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    # 初始化全局上下文
    logger.configure(extra={"request_id": "-"})

    # 1. 准备日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 2. 清除默认处理器
    logger.remove()

    # 3. 统一配置参数提取
    log_format = settings.log_format
    rotation = settings.log_when if settings.log_rotate_type == "time" else settings.log_max_size

    # 通用配置（控制台和文件都支持）
    common_config = {
        "format": log_format,
        "enqueue": True,
        "backtrace": True,
        "diagnose": True
    }

    # 文件专属配置（继承通用配置，并追加文件专属参数）
    file_config = {
        **common_config,
        "rotation": rotation,
        "retention": settings.log_backup_count,
        "compression": "zip",
        "encoding": settings.log_encoding
    }

    # 4. 配置控制台输出 (只传通用配置)
    logger.add(sys.stdout, level=settings.log_level_console, colorize=True, **common_config)

    # 5. 配置业务日志文件 (传文件专属配置)
    logger.add(log_dir / "app.log", level=settings.log_level_app, **file_config)

    # 6. 配置错误日志文件 (传文件专属配置)
    logger.add(log_dir / "error.log", level=settings.log_level_error, **file_config)

    # 7. 彻底接管标准库日志 (Uvicorn, SQLAlchemy, Alembic 等)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # 针对特定模块的级别控制，并切断传播链防止重复输出
    for lib_name in ["sqlalchemy", "alembic", "uvicorn", "uvicorn.access", "uvicorn.error"]:
        lib_logger = logging.getLogger(lib_name)
        lib_logger.handlers = [InterceptHandler()]
        lib_logger.propagate = False