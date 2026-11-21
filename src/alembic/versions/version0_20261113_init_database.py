"""init system schema

Revision ID: version0.20261113
Revises:
Create Date: 2026-11-13 15:24:41.417026+08:00

"""
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Table

from src.core.config import settings

# revision identifiers, used by Alembic.
revision = "version0.20261113"
down_revision = None
branch_labels = None
depends_on = None


def create_user_table() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.String(length=32), nullable=False, comment="主键"),
        sa.Column("username", sa.String(length=50), nullable=False, comment="用户名"),
        sa.Column("zh_name", sa.String(length=150), nullable=True, comment="中文名"),
        sa.Column("en_name", sa.String(length=150), nullable=True, comment="英文名"),
        sa.Column("password", sa.String(length=255), nullable=False, comment="密码"),
        sa.Column("email", sa.String(length=254), nullable=True, comment="邮箱"),
        sa.Column("phone_number", sa.String(length=30), nullable=True, comment="手机号"),
        sa.Column("status", sa.Integer(), nullable=False, comment="0=available 1=unavailable"),
        sa.Column("api_key", sa.String(length=128), nullable=False, comment="API key"),
        sa.Column("create_time", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("update_time", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("delete_time", sa.DateTime(), nullable=True, comment="删除时间"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, comment="软删除标记, 0:否 1:是"),
        sa.Column("first_login", sa.Boolean(), nullable=False, comment="首次登录标记, 0:否 1:是"),
        sa.PrimaryKeyConstraint("id"),
        comment="用户表")

    # 普通索引（autogenerate 会生成）
    op.create_index("ix_user_username", "user", ["username"], unique=False)
    op.create_index("ix_user_email", "user", ["email"], unique=False)
    op.create_index("ix_user_create_time", "user", ["create_time"], unique=False)
    op.create_index("ix_user_is_deleted", "user", ["is_deleted"], unique=False)

    # ⚠️ 手动补：函数唯一索引（autogenerate 不会生成）
    # 注意 sa.text 里不要带最外层括号，op.create_index 会自己包
    op.create_index(
        "uq_user_username_active",
        "user",
        [sa.text("(CASE WHEN is_deleted = 0 THEN username ELSE NULL END)")],
        unique=True,
    )
    op.create_index(
        "uq_user_email_active",
        "user",
        [sa.text("(CASE WHEN is_deleted = 0 THEN email ELSE NULL END)")],
        unique=True,
    )


def rollback_user_table() -> None:
    # 先删函数索引
    op.drop_index("uq_user_email_active", table_name="user")
    op.drop_index("uq_user_username_active", table_name="user")
    # 再删普通索引
    op.drop_index("ix_user_create_time", table_name="user")
    op.drop_index("ix_user_email", table_name="user")
    op.drop_index("ix_user_username", table_name="user")
    op.drop_table("user")


def create_host_table() -> None:
    op.create_table(
        "host",
        sa.Column("id", sa.String(length=32), nullable=False, comment="主键"),
        sa.Column("ip_address", sa.String(length=45), nullable=False, comment="IP地址"),
        sa.Column("username", sa.String(length=50), nullable=False, comment="用户名"),
        sa.Column("password", sa.String(length=255), nullable=False, comment="密码"),
        sa.Column("port", sa.Integer(), nullable=False, comment="端口"),
        sa.CheckConstraint("port >= 1 AND port <= 65535", name="check_port_range"),
        sa.Column("status", sa.Integer(), nullable=False, comment="0=online 1=offline"),
        sa.Column("private_key_path", sa.String(length=255), nullable=False, comment="私钥路径"),
        sa.Column("deploy_path", sa.String(length=255), nullable=False, comment="部署路径"),
        sa.Column("create_time", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("update_time", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("delete_time", sa.DateTime(), nullable=True, comment="删除时间"),
        sa.Column("description", sa.String(length=100), nullable=True, comment="主机描述"),
        sa.PrimaryKeyConstraint("id"),
        comment="主机表",
    )

    op.create_index(
        "uq_host_ip_address",
        "host",
        ["ip_address"],
        unique=True
    )


def rollback_host_table() -> None:
    op.drop_index("uq_host_ip_address", table_name="host")
    op.drop_table(table_name="host")


def create_system_table() -> None:
    system_table: Table = op.create_table(
        "system",
        sa.Column("id", sa.String(length=32), nullable=False, comment="主键"),
        sa.Column("secret_key", sa.String(length=32), nullable=False, comment="sk"),
        sa.PrimaryKeyConstraint("id"),
        comment="系统表",
    )

    op.bulk_insert(
        system_table,
        [{"id": settings.current_app_id, "secret_key": uuid4().hex}])


def rollback_system_table() -> None:
    op.drop_table(table_name="system")


def upgrade() -> None:
    create_user_table()
    create_host_table()
    create_system_table()


def downgrade() -> None:
    rollback_user_table()
    rollback_host_table()
    rollback_system_table()
