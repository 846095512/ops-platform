from loguru import logger
from typing import List

from fastapi import APIRouter, Request
from starlette import status

from src.core.dependency import UserServiceDep
from src.models.user import User
from src.schemas.response import ApiResponse
from src.schemas.user import UserCreate

# 1. 创建 router，定义好前缀和标签
router = APIRouter(
    prefix="/user",
    tags=["用户管理"]  # 在 Swagger 文档里会分类显示
)



@router.post("/create", response_model=ApiResponse[List[User]], status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, service: UserServiceDep, request: Request):
    user: User = await service.create_user(user_in)
    return user


@router.get("/info", status_code=status.HTTP_200_OK)
async def read_users(username, password):
    from schemas.jwt_payload import JwtPayload
    from src.core.security import create_access_token
    payload = JwtPayload(sub="user_12345")
    logger.info(payload)

    # 2. 直接调用，无需传入 secret_key
    token = await create_access_token(payload, jwt_token_expire_min=60)
    logger.info(token)