from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import security
from src.core.storge import BackendStorge, get_storage
from src.service.user_service import UserService


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


def get_backend() -> BackendStorge:
    return get_storage()


def get_secret_key_dep() -> str:
    if not security.SECRET_KEY:
        raise HTTPException(status_code=500, detail="Secret key not initialized")
    return security.SECRET_KEY


UserServiceDep = Annotated[UserService, Depends(get_user_service)]

DbSession = Annotated[AsyncSession, Depends(get_db)]
