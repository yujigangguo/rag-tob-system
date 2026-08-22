"""文档模型(知识库下上传的离线文件)。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    kb_id: Mapped[int] = mapped_column(ForeignKey("knowledge_bases.id"), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)  # 上传后的本地路径
    file_type: Mapped[str] = mapped_column(String(16), nullable=False)    # pdf/pptx/md/txt/png/jpg
    # 解析状态:pending / parsing / completed / failed
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    error_msg: Mapped[str] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
