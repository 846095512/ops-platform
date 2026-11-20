import ipaddress
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from pydantic import field_validator, NaiveDatetime
from sqlmodel import Field, SQLModel

from src.core.config import Settings, get_settings

settings: Settings = get_settings()


class Host(SQLModel, table=True):
    __tablename__ = "host"
    id: str = Field(default_factory=lambda: uuid4().hex,
                    primary_key=True,
                    max_length=32)
    ip_address: str = Field(max_length=45, unique=True, description="IP地址")
    username: str = Field(max_length=50, description="主机用户名")
    password: str = Field(max_length=255, description="主机密码")
    port: int = Field(ge=1, le=65535, description="主机端口")
    status: int = Field(ge=0, le=1, description="主机状态 0=online 1=offline")
    private_key_path: str = Field(max_length=255, description="私钥路径")
    deploy_path: str = Field(max_length=255, description="部署路径")
    create_time: NaiveDatetime = Field(default_factory=lambda: datetime.now(ZoneInfo(settings.zone_info))
                                       , description="创建时间")
    update_time: NaiveDatetime | None = Field(default=None, description="更新时间")
    delete_time: NaiveDatetime | None = Field(default=None, description="删除时间")
    description: str = Field(max_length=100, default=None, description="主机描述")

    @field_validator("ip_address", mode="before")
    @classmethod
    def check_ip(cls, ip: str):
        ip = ip.strip()
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            raise ValueError(f"invalid IP address: {ip!r}")
        return ip
