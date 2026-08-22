"""对话相关 schema。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ChatSessionCreate(BaseModel):
    name: str = Field("新对话", max_length=128, description="会话名称")


class ChatSessionOut(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageOut(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    """一次问答请求(流式)。"""
    session_id: int | None = Field(None, description="会话 id,为空则新建会话")
    session_name: str | None = Field(None, max_length=128, description="新建会话时的名称")
    question: str = Field(..., min_length=1, description="用户问题")
    kb_ids: list[int] = Field(..., min_length=1, description="勾选的知识库 id 列表")
    model: str = Field("qwen-max", description="大模型")
    temperature: float = Field(0.7, ge=0, le=2, description="温度")
    top_p: float = Field(0.8, ge=0, le=1, description="Top P")
    max_tokens: int = Field(2048, ge=1, le=8192, description="最长输出 token 数")
    history_rounds: int = Field(5, ge=0, le=20, description="历史对话轮数")
