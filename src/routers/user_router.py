from typing import List

from fastapi import APIRouter, Request
from loguru import logger
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


@router.post("/hosts/connect", response_model=ApiResponse)
async def connect_and_save_host(
        request: Request,
        service: UserServiceDe):
    """
    测试主机连接，成功后生成密钥、下发公钥并保存主机信息
    """
    # 1. 检查主机是否已存在
    result = await db.execute(select(Host).where(Host.ip == request.ip))
    existing_host = result.scalar_one_or_none()

    if existing_host:
        # 如果已存在，这里可以选择更新密码并重新下发密钥，或者直接报错
        # 为了演示，我们直接报错
        raise HTTPException(status_code=400, detail=f"主机 {request.ip} 已被纳管")

    # 2. 创建主机记录（先入库获取 ID，用于生成专属密钥文件名）
    new_host = Host(ip=request.ip, port=request.port, username=request.username)
    db.add(new_host)
    await db.commit()
    await db.refresh(new_host)  # 获取自增 ID

    try:
        # 3. 调用 SSH 管理器：测试密码连接 -> 生成密钥 -> 下发公钥
        private_key_path = await ssh_manager.test_connection_and_bootstrap(
            ip=request.ip,
            port=request.port,
            username=request.username,
            password=request.password,
            host_id=new_host.id
        )

        # 4. 更新主机状态为在线，并保存私钥路径和认证方式
        new_host.status = "online"
        new_host.auth_type = "key"
        new_host.private_key_path = private_key_path
        await db.commit()
        await db.refresh(new_host)

        return new_host

    except Exception as e:
        # 如果连接或下发失败，删除刚才创建的脏数据
        await db.delete(new_host)
        await db.commit()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/login")
async def login(username: str, password: str):
    if username != "admin" or password != "123456":
        return {"code": 400, "message": "账号密码错误"}
    payload = {
        "sub": username,
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(hours=2),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return {"code": 200, "token": token}
