import time
from contextvars import ContextVar
from uuid import uuid4

from fastapi import Request, Response, HTTPException
from loguru import logger
from starlette.datastructures import Address

from src.core.security import verify_token, verify_apikey
from src.schemas.response import ApiResponse
from src.core.config import settings

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


def _unauthorized() -> ApiResponse:
    return ApiResponse(code=401, message="", data=None)


async def api_auth_middleware(request: Request, call_next):
    path = request.url.path

    # 0. CORS 预检放行
    if request.method == "OPTIONS":
        return await call_next(request)

    # 1. 白名单放行
    if any(path.startswith(w) for w in settings.WHITE_LIST):
        return await call_next(request)

    # 2. 提取 token
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
    token = token or request.query_params.get("token") or request.headers.get("X-Token")

    # 3. 提取 apikey（query 参数，兼容 Header X-API-Key）
    apikey = request.query_params.get("apikey") or request.headers.get("X-API-Key")

    try:
        if token:
            request.state.auth_type = "token"
            request.state.user = verify_token(token)
        elif apikey:
            request.state.auth_type = "apikey"
            request.state.user = verify_apikey(apikey)
        else:
            return _unauthorized()
    except HTTPException as e:
        raise e
    return await call_next(request)
