from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import jwt
from jwt import PyJWTError
from loguru import logger

from src.core.config import Settings, get_settings
from src.schemas.jwt_payload import JwtPayload

settings: Settings = get_settings()
algorithm: str = "HS256"


class SecurityManager:
    _instance = None
    _secret_key: str | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def secret_key(self) -> str:
        if not self._secret_key:
            raise RuntimeError("Secret key not initialized")
        return self._secret_key

    def set_secret_key(self, key: str) -> None:
        self._secret_key = key

    def clear(self) -> None:
        self._secret_key = None


security = SecurityManager()


async def create_access_token(payload: JwtPayload, jwt_token_expire_min: int | float = 30) -> str:
    try:
        secret_key = security.secret_key
    except RuntimeError as e:
        logger.error(f"Failed to create token: {e}")
        raise ValueError("System not ready, secret key missing.")
    expire_time = datetime.now(ZoneInfo(settings.zone_info)) + timedelta(minutes=jwt_token_expire_min)
    payload.exp = expire_time.timestamp()
    return jwt.encode(payload.model_dump(exclude_none=True), secret_key, algorithm=algorithm)


async def verify_token(token: str) -> bool:
    try:
        secret_key = security.secret_key
    except RuntimeError:
        raise "System not ready, secret key missing."

    try:
        payload = jwt.decode(token, secret_key, algorithms=algorithm)
        if not payload.get("sub"):
            raise PyJWTError("Token missing 'sub' claim")
        return payload
    except PyJWTError as e:
        logger.warning(f"Verify JWT Token Failed, Error: {e}")
        raise "Invalid or expired token"


async def verify_apikey(apikey: str) -> str:
    key = apikey
    if not key:
        pass
    return key
