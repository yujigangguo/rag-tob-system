"""文档与文档块相关 schema。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: int
    kb_id: int
    filename: str
    file_type: str
    status: str
    error_msg: str | None
    chunk_count: int
    version: int = 1   # 当前版本号(重传内容变化 +1)
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentVersionOut(BaseModel):
    version: int
    parent_count: int = 0
    is_current: bool = False


class ChunkOut(BaseModel):
    id: int
    kb_id: int
    document_id: int
    content: str
    chunk_index: int
    parent_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChunkUpdate(BaseModel):
    """文档块编辑(更新文本后需重新向量化)。"""
    content: str = Field(..., min_length=1, description="新的文本内容")


class ParseConfig(BaseModel):
    """文档解析参数。"""
    chunk_size: int | None = Field(None, ge=50, le=4000)
    chunk_overlap: int | None = Field(None, ge=0, le=1000)
