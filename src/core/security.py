from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import jwt
from jwt import PyJWTError
from loguru import logger

from src.core.tools import get_secret_key
from src.core.config import settings
from src.schemas.jwt_payload import JwtPayload


async def create_access_token(payload: JwtPayload) -> str:
    expire_time = datetime.now(ZoneInfo(settings.zone_info)) + timedelta(minutes=settings.jwt_token_expire)
    payload.exp = expire_time.timestamp()
    return jwt.encode(payload.model_dump(exclude_none=True), get_secret_key(), algorithm=settings.algorithm)


async def verify_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=settings.algorithm)
        if not payload.get("sub"):
            raise PyJWTError("Token missing 'sub' claim")
        return payload
    except PyJWTError as e:
        logger.warning(f"Verify JWT Token Failed, Error: {e}")
        raise "Invalid or expired token"


async def verify_apikey(apikey: str) -> str:
    # TODO 从db中获取apikey与传参对比 一致为true 不一致为fasle
    key = apikey
    if not key:
        pass
    return key
