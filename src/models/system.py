from uuid import uuid4

from sqlmodel import Field, SQLModel

from src.core.config import get_settings

settings = get_settings()


class System(SQLModel, table=True):
    __tablename__ = "system"
    id: str = Field(default_factory=lambda: uuid4().hex,
                    primary_key=True,
                    max_length=32,
                    description="ID标识")
    secret_key: str = Field(default_factory=lambda: uuid4().hex, max_length=32, description="sk")
