import time
from contextvars import ContextVar
from uuid import uuid4

from loguru import logger
from fastapi import Request, Response
from starlette.datastructures import Address

from src.core.config import get_settings, Settings

settings: Settings = get_settings()
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


async def api_logging_middleware(request: Request, call_next) -> Response:
    start_time: float | int = time.perf_counter()
    client_host: Address | str = (
        getattr(request.client, "host", "unknown") if request.client else "unknown"
    )
    request_id = request.headers.get("X-Request-ID", uuid4().hex)
    request_id_ctx.set(request_id)
    with logger.contextualize(request_id=request_id):
        logger.debug(
            f"API Enter request_id={request_id} "
            f"request_method={request.method} "
            f"request_url={request.url} "
            f"request_client={client_host}"
        )

        try:
            api_response = await call_next(request)
            api_response.headers["X-Request-ID"] = request_id
            elapsed_ms: float | int = (time.perf_counter() - start_time) * 1000
            api_response.headers["X-Request-ID"] = request_id
            logger.debug(
                f"API Exit request_id={request_id} "
                f"request_method={request.method} "
                f"request_url={request.url} "
                f"status_code={api_response.status_code} "
                f"duration={elapsed_ms:.2f}ms"
            )
            return api_response
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                f"API Unhandled Exception request_id={request_id} "
                f"request_method={request.method} "
                f"request_url={request.url} "
                f"raised_error={type(e).__name__} "
                f"duration={elapsed_ms:.2f}ms"
            )
            raise

"""
async def dispatch(self, request: Request, call_next):
    # 1. 白名单路径直接放行
    if _is_public_path(request.url.path):
        return await call_next(request)

    # 2. 提取凭证
    auth_header = request.headers.get("Authorization")
    api_key = request.headers.get("X-API-Key")

    user_context = None

    # 3. JWT 认证（前端用户）
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        user_context = await verify_jwt_token(token)

    # 4. API Key 认证（第三方）
    elif api_key:
        user_context = await validate_api_key(api_key)

    # 5. 认证失败
    if user_context is None:
        return False

    # 6. 将用户上下文注入 request.state，供下游使用
    request.state.user = user_context

    # 7. 可选：将身份信息透传到请求头（微服务场景）
    request.scope["headers"] = [
        *request.scope["headers"],
        (b"x-user-id", user_context.user_id.encode()),
        (b"x-auth-type", user_context.auth_type.value.encode()),
    ]

    return await call_next(request)


def _is_public_path(self, path: str) -> bool:
    白名单：健康检查、登录、注册等公开接口
    public_prefixes = settings.PUBLIC_PATHS
    return any(path.startswith(prefix) for prefix in public_prefixes)
"""