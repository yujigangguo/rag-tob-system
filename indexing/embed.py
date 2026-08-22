"""Embedding 封装:通义 text-embedding(走 DashScope 原生接口)。

注意:embedding 模型必须与 LLM 分开,使用专门的中文 embedding 模型。
"""
from __future__ import annotations

from langchain_core.embeddings import Embeddings

from config.settings import settings


def get_embeddings() -> Embeddings:
    """返回 embedding 实例(通义 text-embedding-v3)。

    使用 langchain-community 的 DashScopeEmbeddings,直接调用 DashScope 原生
    TextEmbedding API,避免 OpenAI 兼容层的 tiktoken/token-ID 问题
    (DashScope 的 OpenAI 兼容 embedding 接口不接受 token ID 输入)。
    """
    from langchain_community.embeddings import DashScopeEmbeddings

    return DashScopeEmbeddings(
        model=settings.embedding_model,
        dashscope_api_key=settings.embedding_api_key,
    )
