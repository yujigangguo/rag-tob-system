"""大模型:通义千问 qwen-max(OpenAI 兼容接口,支持流式)。"""
from __future__ import annotations

from config.settings import settings


def get_llm(
    model: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
    streaming: bool = True,
):
    """构造 ChatOpenAI 实例(指向通义 DashScope)。"""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model or settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=temperature if temperature is not None else settings.llm_temperature,
        top_p=top_p if top_p is not None else settings.llm_top_p,
        max_tokens=max_tokens or settings.llm_max_tokens,
        streaming=streaming,
    )
