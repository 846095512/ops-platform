from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from src.core.config import settings


class JwtPayload(BaseModel):
    sub: str = Field(..., max_length=32, description="用户ID")
    exp: int | float = Field(default=30, description="过期时间")
    iat: int | float = Field(
        default_factory=lambda: datetime.now(ZoneInfo(settings.zone_info)).timestamp(),
        description="签发时间")
    iss: str = Field(default="ops-platform", description="签发者")
    aud: str = Field(default="ops-client", description="受众")
    jti: str = Field(default_factory=lambda: uuid4().hex, max_length=32, description="Token 唯一 ID")
