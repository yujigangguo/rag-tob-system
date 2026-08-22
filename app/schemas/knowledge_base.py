"""知识库相关 schema。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="知识库名称")
    description: str | None = Field(None, max_length=500, description="描述")
    retrieval_type: str = Field("hybrid", pattern="^(dense|hybrid)$", description="检索方式:dense/hybrid")
    chunk_size: int = Field(500, ge=50, le=4000, description="文本切块大小")
    chunk_overlap: int = Field(50, ge=0, le=1000, description="重叠大小")


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = Field(None, max_length=500)
    retrieval_type: str | None = Field(None, pattern="^(dense|hybrid)$")
    chunk_size: int | None = Field(None, ge=50, le=4000)
    chunk_overlap: int | None = Field(None, ge=0, le=1000)


class KnowledgeBaseOut(BaseModel):
    id: int
    name: str
    description: str | None
    retrieval_type: str
    chunk_size: int
    chunk_overlap: int
    doc_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
