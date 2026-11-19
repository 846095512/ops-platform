from typing import Generic, TypeVar, List, Optional

from pydantic import BaseModel, Field

from src.core.app_enum import BizStatus

T = TypeVar("T")


class PaginatedData(BaseModel, Generic[T]):
    """作为 data 内层的数据结构，包含分页信息和列表"""
    items: List[T] = Field(..., description="当前页数据列表")
    total: int = Field(..., description="数据总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数(最后一页)")


class ApiResponse(BaseModel, Generic[T]):
    """统一响应结构"""
    code: int = Field(default=BizStatus.SUCCESS.code, description="业务状态码")
    message: str = Field(default=BizStatus.SUCCESS.msg, description="提示信息")
    data: Optional[T] = Field(default=None, description="业务数据(分页时为 PaginatedData 结构)")


def create_paginated_response(
        items: List[T],
        total: int,
        page: int,
        page_size: int,
        code: int = BizStatus.SUCCESS.code,
        message: str = BizStatus.SUCCESS.msg,
) -> ApiResponse[PaginatedData[T]]:
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    data = PaginatedData(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
    return ApiResponse(code=code, message=message, data=data)
