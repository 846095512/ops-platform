from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import quote_plus

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


@lru_cache
class Settings(BaseSettings):
    """
        全局配置获取
    """
    current_app_id: str = Field(default="opsplatform74379acad94e5b5ab9999", description="本应用id")
    algorithm: str = Field(default="HS256", description="加密算法类型")
    jwt_token_expire: int = Field(default=30, description="jwt token过期时间,默认30分钟")
    database_username: str | None = Field(default=None, description="数据库用户")
    database_password: str | None = Field(default=None, description="数据库密码")
    database_host: str | None = Field(default=None, description="数据库地址")
    database_port: int | None = Field(default=None, description="数据库端口")
    database_name: str | None = Field(default=None, description="库名")

    database_driver: str = Field(default="aiomysql", description="数据库驱动")
    database_type: str = Field(default="mysql", description="数据库类型")
    database_connect_timeout: int = Field(default=30, description="连接超时时间")
    database_charset: str = Field(default="utf8mb4", description="数据库字符集")

    database_url: str | None = Field(default=None, description="数据库连接串")
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
    log_max_size: int = Field(default=20 * 1024 ** 2, description="日志文件大小(size轮转生效)")
    log_when: str = Field(default="midnight", description="时间轮转单位(time轮转生效), 如 midnight, H, D")
    log_level_console: str = Field(default="INFO", description="控制台日志级别")
    log_level_app: str = Field(default="INFO", description="业务文件日志级别")
    log_level_error: str = Field(default="ERROR", description="错误文件日志级别")
    log_level_root: str = Field(default="INFO", description="根文件日志级别")
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

    default_page_lines: int = Field(default=200, description="日志首屏行数,前端可按屏高覆盖")
    max_page_lines: int = Field(default=1000, description="一页最大行数")
    max_line_chars: int = Field(default=4000, description="单行最大字符数")
    max_search_lines: int = Field(default=500, description="搜索单页最大匹配行")

    deploy_timeout: int = Field(default=3600, description="部署超时时间,默认1小时")
    line_count_ttl_sec: int = Field(default=300, description="总行数缓存时间,默认5分钟")
    deploy_log_max_bytes: int = Field(default=10 * 1024 ** 3, description="部署日志最大保存大小,默认10G")
    deploy_log_keep_days: int = Field(default=30, description="部署日志最大保存时间,默认30天")
    buffer_max: int = Field(default=500, description="缓冲区大小")

    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[1] / ".env",
                                      env_file_encoding="utf-8",
                                      case_sensitive=False,
                                      extra="ignore")

    @model_validator(mode="after")
    def validate_and_build_url(self):
        """
        验证提供的数据库参数
        如果提供了完整的database_url,直接使用database_url作为数据库连接url
        没有database_url,则要求提供数据库连接参数
        :return: 数据库连接串 如: mysql+aiomysql://user:password@host:port/database_name
        """
        if self.database_url:
            return self

        required_fields = {
            "database_username": self.database_username,
            "database_password": self.database_password,
            "database_host": self.database_host,
            "database_port": self.database_port,
            "database_name": self.database_name,
        }

        missing = [k for k, v in required_fields.items() if v is None]
        if missing:
            raise ValueError(
                f"If database_url is not provided, the following configuration must be provided: {','.join(missing)}")
        password: str = self.database_password or ""
        self.database_url = (
            f"{self.database_type}+{self.database_driver}://{self.database_username}"
            f":{quote_plus(password)}@"
            f"{self.database_host}:{self.database_port}/"
            f"{self.database_name}"
            f"?charset={self.database_charset}&connect_timeout={self.database_connect_timeout}"
        )
        return self


settings = Settings()
