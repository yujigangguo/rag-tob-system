"""向量化:通义 embedding(DashScope 原生接口)。"""
from __future__ import annotations

from functools import lru_cache

from langchain_core.embeddings import Embeddings

from config.settings import settings


@lru_cache
def get_embeddings() -> Embeddings:
    """返回单例 embedding 实例(通义 text-embedding)。"""
    from langchain_community.embeddings import DashScopeEmbeddings

    return DashScopeEmbeddings(
        model=settings.embedding_model,
        dashscope_api_key=settings.embedding_api_key,
    )
