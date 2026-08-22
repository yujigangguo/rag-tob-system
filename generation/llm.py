"""大模型封装:DeepSeek(通过 OpenAI 兼容接口)。"""
from __future__ import annotations

from functools import lru_cache

from config.settings import settings


@lru_cache
def get_llm():
    """返回单例 ChatOpenAI 实例(指向 DeepSeek)。

    首次调用时根据 settings 构造,之后复用同一个实例。
    """
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
    )
