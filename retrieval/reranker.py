"""重排序:用专门的 rerank 模型对召回结果精排,保留最相关的 top_n。"""
from __future__ import annotations

from typing import List

from langchain_core.documents import Document

from config.settings import settings


def rerank(query: str, documents: List[Document], top_n: int | None = None) -> List[Document]:
    """用通义 gte-rerank 精排(走 DashScope 原生接口)。

    未配置 rerank_api_key 时,原样返回前 top_n 条(跳过重排)。
    """
    top_n = top_n or settings.final_top_k
    if not documents:
        return []

    if not settings.rerank_api_key:
        return documents[:top_n]

    import dashscope

    resp = dashscope.TextReRank.call(
        api_key=settings.rerank_api_key,
        model=settings.rerank_model,
        query=query,
        documents=[d.page_content for d in documents],
        top_n=top_n,
    )
    if resp.status_code != 200:
        print(f"[rerank 失败] code={resp.code}, message={resp.message}; 退回原顺序")
        return documents[:top_n]

    results = resp.output.results  # 每项含 index / relevance_score
    reranked = [documents[item.index] for item in sorted(results, key=lambda x: x.index)]
    return reranked[:top_n]
