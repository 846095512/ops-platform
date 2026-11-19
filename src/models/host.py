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
    ip_address: str = Field(max_length=45, unique=True)
    username: str = Field(max_length=50)
    password: str = Field(max_length=255)
    port: int = Field(ge=1, le=65535)
    status: int = Field(ge=0, le=1, description="0=online 1=offline")
    secret_key: str = Field(max_length=64)
    deploy_path: str = Field(max_length=255)
    create_time: NaiveDatetime = Field(default_factory=lambda: datetime.now(ZoneInfo(settings.zone_info)))
    update_time: NaiveDatetime | None = Field(default=None)
    delete_time: NaiveDatetime | None = Field(default=None)
    description: str = Field(max_length=100, default=None)

    @field_validator("ip_address", mode="before")
    @classmethod
    def check_ip(cls, ip: str):
        ip = ip.strip()
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            raise ValueError(f"invalid IP address: {ip!r}")
        return ip
