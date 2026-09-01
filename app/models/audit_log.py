"""审计日志模型。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False)  # 操作人用户名
    action: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # 操作类型
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)  # 操作对象类型
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 操作对象ID
    target_name: Mapped[str | None] = mapped_column(String(128), nullable=True)  # 操作对象名称
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)  # 详细信息
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IP地址
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
