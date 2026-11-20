from pydantic import BaseModel, Field


class HostCreate(BaseModel):
    ip_address: str = Field(..., max_length=45, description="用户名")
    username: str = Field(..., max_length=32, description="用户名")
    password: str = Field(..., max_length=255, description="密码")
    port: int = Field(ge=1, le=65535, description="端口")
    private_key_path: str = Field(..., max_length=255, description="私钥路径")
    deploy_path: str = Field(..., max_length=255, description="部署路径")
