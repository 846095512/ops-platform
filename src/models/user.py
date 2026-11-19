from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from pydantic import EmailStr, NaiveDatetime
from pydantic_extra_types.phone_numbers import PhoneNumber
from sqlalchemy import Index, text, event
from sqlalchemy.orm import with_loader_criteria, Session
from sqlmodel import Field, SQLModel

from src.core.config import Settings, get_settings

settings: Settings = get_settings()


class User(SQLModel, table=True):
    __tablename__ = "user"
    __table_args__ = (
        Index(
            "uq_user_username_active",
            text("(CASE WHEN is_deleted = 0 THEN username ELSE NULL END)"),
            unique=True,
        ),
        Index(
            "uq_user_email_active",
            text("(CASE WHEN is_deleted = 0 THEN email ELSE NULL END)"),
            unique=True,
        ),
        Index(
            "uq_user_phone_active",
            text("(CASE WHEN is_deleted = 0 THEN phone_number ELSE NULL END)"),
            unique=True,
        ),
        {"comment": "用户表"},
    )
    id: str = Field(default_factory=lambda: uuid4().hex, max_length=32, primary_key=True, description="主键")
    username: str = Field(max_length=50, index=True, description="用户名")
    zh_name: str | None = Field(max_length=150, description="用户中文名")
    en_name: str | None = Field(max_length=150, description="用户英文名")
    password: str = Field(max_length=255, description="密码")
    email: EmailStr | None = Field(max_length=255, index=True, description="邮箱")
    phone_number: PhoneNumber | None = Field(max_length=30, index=True, description="手机号")
    status: int = Field(ge=0, le=1, description="0=available 1=unavailable")
    api_key: str = Field(max_length=128, description="API key")
    create_time: NaiveDatetime = Field(default_factory=lambda: datetime.now(ZoneInfo(settings.zone_info)), index=True,
                                       description="创建时间")
    update_time: NaiveDatetime | None = Field(default=None,
                                              sa_column_kwargs={"onupdate": datetime.now(ZoneInfo(settings.zone_info))},
                                              description="更新时间")
    delete_time: NaiveDatetime | None = Field(default=None, description="删除时间")
    is_deleted: bool = Field(default=False, index=True, description="软删除标记, 0:否 1:是")
    first_login: bool = Field(default=False, description="第一次登录标记")

    def soft_delete(self) -> None:
        """软删除当前用户"""
        self.is_deleted = True
        self.delete_time = datetime.now()

    def restore(self) -> None:
        """恢复软删除的用户"""
        self.is_deleted = False
        self.delete_time = None


@event.listens_for(Session, "do_orm_execute")
def _filter_soft_deleted(execute_state):
    """全局自动过滤软删除数据，需查已删除时用 execution_options(include_deleted=True)"""
    if not execute_state.is_select:
        return
    if execute_state.execution_options.get("include_deleted", False):
        return
    execute_state.statement = execute_state.statement.options(
        with_loader_criteria(
            User,
            lambda cls: cls.is_deleted == False,
            include_aliases=True,
        )
    )
