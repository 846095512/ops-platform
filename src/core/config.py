from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from loguru import logger
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(
        default="mysql+aiomysql://root:123456@localhost:3306/ops?charset=utf8mb4&connect_timeout=10")
    database_charset: str = Field(default="utf8mb4", description="数据库字符集")
    database_collation: str = Field(default="utf8mb4_unicode_ci", description="排序规则")
    database_pool_size: int = Field(default=10, description="常驻连接数"
                                                            "公式: (并发请求数 / 每请求平均查询数) * 1.5")
    database_max_overflow: int = Field(default=10,
                                       description="突发时允许额外创建的临时连接数,"
                                                   "总上限 = pool_size + max_overflow")
    database_pool_recycle: int = Field(default=1800,
                                       description="连接最大存活秒数, 到期后重建, 应小于 MySQL 的 wait_timeout(默认 28800 秒)")
    database_echo: bool = Field(default=False, description="打印所有SQL, 生产关闭")
    database_pool_use_lifo: bool = Field(default=True,
                                         description="默认False(FIFO),设为 True 时,连接池会优先复用最近归还的连接(后进先出)"
                                                     "在非高峰时段有助于减少池中闲置的连接数,让 MySQL 服务端能回收空闲连接,从而降低服务端连接压力")
    database_pool_pre_ping: bool = Field(default=True,
                                         description="从池中取出连接前先 ping 一次, 自动剔除已断开的连接(如 MySQL 侧超时断开)")
    database_pool_timeout: int = Field(default=30, description="从池中获取连接的最长等待秒数,超时抛异常")
    migration_dir: str = Field(default="src/alembic/sql", description="数据库升级sql目录")

    log_rotate_type: str = Field(
        default="size",
        description="日志轮转类型, 可选: size(按大小) 或 time(按时间)"
    )
    log_max_size: int = Field(default=20 * 1024 * 1024, description="日志文件大小(size轮转生效)")
    log_when: str = Field(default="midnight", description="时间轮转单位(time轮转生效), 如 midnight, H, D")
    log_level_console: str = Field(default="INFO", description="控制台日志级别")
    log_level_app: str = Field(default="INFO", description="业务文件日志级别")
    log_level_error: str = Field(default="ERROR", description="错误文件日志级别")
    log_backup_count: int = Field(default=15, description="日志文件保留个数(时间轮转时即为保留天数)")
    log_encoding: str = Field(default="utf-8", description="日志文件编码")
    log_format: str = Field(
        default=
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level:<7}</level> | "
        "<magenta>request_id:{extra[request_id]}</magenta> | "
        "process_id:<magenta>{process}</magenta> | "
        "thread_id:<yellow>{thread.id}</yellow> | "
        "thread_name:<yellow>{thread.name}</yellow> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>",
        description="日志格式化字符串"
    )

    zone_info: str = Field(default="Asia/Shanghai", description="时区")

    backend_storge: Literal["local", "ceph", "s3"] = Field(default="local", description="文件存储类型")
    local_upload_dir: Path = Field(default=Path(__name__).parent / "data/upload", description="本地存储目录")

    s3_endpoint_url: str | None = Field(default=None, description="s3 地址, Ceph填写, aws s3不填")
    s3_access_key: str = Field(default="", description="s3 ak")
    s3_secret_key: str = Field(default="", description="s3 sk")
    s3_bucket: str = Field(default="", description="s3 bucket")
    s3_region: str = Field(default="", description="s3 region")

    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[1] / ".env",
                                      env_file_encoding="utf-8",
                                      case_sensitive=False,
                                      extra="ignore")

    @field_validator("database_url")
    @classmethod
    def _validate_database_url(cls,
                               connection_url: str) -> str:
        parsed_url = urlparse(connection_url)
        if not parsed_url.scheme.startswith("mysql"):
            raise ValueError(f"database_url need start with mysql，current is: {parsed_url.scheme}")
        if not parsed_url.path.lstrip("/"):
            raise ValueError(f"database_url need contain database name, current is: {connection_url}")
        return connection_url

    @property
    def database_name(self) -> str:
        """从 database_url 解析出的库名"""
        return urlparse(self.database_url).path.lstrip("/")

    @property
    def server_url(self) -> str:
        """不含库名的连接串，用于建库"""
        parsed_url = urlparse(self.database_url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except Exception as e:
        logger.exception("app config file load error, plz check .env file......")
        raise e
