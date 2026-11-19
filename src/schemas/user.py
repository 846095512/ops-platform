from pydantic import BaseModel, Field, EmailStr, NaiveDatetime
from pydantic_extra_types.phone_numbers import PhoneNumber


class UserCreate(BaseModel):
    username: str = Field(..., max_length=32, description="用户名")
    password: str = Field(..., max_length=255, description="密码")
    email: EmailStr | None = Field(default=None, max_length=255, description="邮箱")
    zh_name: str | None = Field(default=None, max_length=150, description="中文名")
    en_name: str | None = Field(default=None, max_length=150, description="英文名")
    phone_number: PhoneNumber | None = Field(default=None, description="手机号")


class UserUpdate(BaseModel):
    password: str | None = Field(default=None, max_length=255, description="密码")
    email: EmailStr | None = Field(default=None, max_length=255, description="邮箱")
    phone_number: PhoneNumber | None = Field(default=None, description="手机号")


class UserDelete(BaseModel):
    id: str = Field(..., max_length=32, description="用户 ID")


class UserQuery(BaseModel):
    username: str | None = Field(default=None, max_length=32, description="用户名")
    email: EmailStr | None = Field(default=None, max_length=255, description="邮箱")
    phone_number: PhoneNumber | None = Field(default=None, max_length=30, description="手机号")
    status: int | None = Field(default=None, ge=0, le=1, description="用户状态")
    create_time: NaiveDatetime | None = Field(default=None, description="创建时间")
    update_time: NaiveDatetime | None = Field(default=None, description="更新时间")
