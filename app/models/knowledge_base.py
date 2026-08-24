"""知识库模型。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)  # 创建者
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True, nullable=False)  # 所属部门
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # 检索方式:dense(稠密向量) / hybrid(混合检索)
    retrieval_type: Mapped[str] = mapped_column(String(16), default="dense", nullable=False)
    chunk_size: Mapped[int] = mapped_column(Integer, default=500, nullable=False)   # 子块大小(检索粒度)
    chunk_overlap: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    parent_chunk_size: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)  # 父块大小(上下文粒度)
    doc_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
