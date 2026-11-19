from loguru import logger
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette import status

from src.core.app_enum import BizStatus


class AuthException(Exception):
    def __init__(self, name: str):
        self.name = name

def setup_exception_handlers(app: FastAPI) -> None:
    """集中注册全局异常处理器
    validation_exception_handler 记录 Pydantic 校验错误日志
    http_exception_handler  记录 Http 请求的错误日志
    auth_exception_handler 认证处理
    global_exception_handler 全局异常兜底
    """

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        logger.warning(f"Parameter Validation Error: {request.method} {request.url.path} - {exc.errors()}")
        return JSONResponse(
            status_code=BizStatus.PARAM_ERROR.code,
            content={
                "code": BizStatus.PARAM_ERROR.code,
                "message": BizStatus.PARAM_ERROR.msg
            }
        )

    @app.exception_handler(AuthException)
    async def auth_exception_handler(request: Request, exc: AuthException):
        logger.info(f"Auth exception: ")
        return JSONResponse(
            status_code=BizStatus.USER_NOT_FOUND.code,
            content={
                "code": BizStatus.USER_NOT_FOUND.code,
                "message": BizStatus.USER_NOT_FOUND.msg
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.info(f"HTTP exception: {request.method} {request.url.path} - {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "message": exc.detail
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"System Uncaught Exception: {request.method} {request.url.path} "
                         f"Exception Type: {type(exc).__name__}, Exception Message: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": BizStatus.BIZ_ERROR.code,
                "message": BizStatus.BIZ_ERROR.msg
            }
        )
