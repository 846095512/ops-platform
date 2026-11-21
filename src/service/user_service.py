import hashlib
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import select, CursorResult
from sqlmodel import col

from src.core.config import settings
from src.models.user import User
from src.schemas.user import UserCreate


class UserService:

    def __init__(self, db=None):
        self.db = db

    async def create_user(self, user_in: UserCreate) -> User:
        result: CursorResult = await  self.db.execute(select(User).where(col(User.username) == user_in.username))
        if result.scalar_one_or_none():
            raise ValueError("用户名已存在")

        hashed_pwd: str = hashlib.sha256(user_in.password.encode()).hexdigest()
        db_user: User = User(id=uuid4().hex, username=user_in.username, password=hashed_pwd, email=user_in.email,
                             zh_name=user_in.zh_name, phone_number=user_in.phone_number,
                             en_name=user_in.en_name, status=0, api_key=uuid4().hex,
                             create_time=datetime.now(ZoneInfo(settings.zone_info)))

        # 3. 入库
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user
