"""用户模型。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # 角色:super_admin(系统管理员,所有部门)/ dept_admin(部门管理员,本部门)/ employee(员工,默认)
    role: Mapped[str] = mapped_column(String(16), default="employee", nullable=False)
    # 所属部门(super_admin 可为空;dept_admin / employee 必填)
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True, index=True
    )
    # 个人信息
    nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)  # 昵称
    email: Mapped[str | None] = mapped_column(String(128), nullable=True)    # 邮箱
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)      # 头像URL(base64或链接)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # 账号是否启用
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
