"""查询改写:把口语化/模糊/指代不清的问题改写成更适合检索的表达。"""
from __future__ import annotations

from generation.llm import get_llm

_REWRITE_PROMPT = """把下面的用户问题改写成一个更清晰、更适合文档检索的查询。
要求:保留原意、补充必要关键词、去除语气词和指代不清的表达。
只输出改写后的单个问题,不要任何解释。

原问题:{question}
改写后:"""


def rewrite_query(question: str) -> str:
    """用 LLM 改写查询。

    简单问题可直接用原问题;本函数对口语化、含指代的问题效果更好。
    """
    question = question.strip()
    if not question:
        return question
    resp = get_llm().invoke(_REWRITE_PROMPT.format(question=question))
    return resp.content.strip()
