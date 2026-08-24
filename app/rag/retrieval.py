"""检索:稠密向量检索 + 混合检索(BM25),支持多知识库。"""
from __future__ import annotations

import re
from typing import List

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from app.logging_config import get_logger
from app.rag.vector_store import get_vector_store
from config.settings import settings

logger = get_logger(__name__)


def tokenize(text: str) -> List[str]:
    """简单分词:中文按单字、英文按单词、数字保留。"""
    return re.findall(r"[\u4e00-\u9fff]|[a-zA-Z0-9]+", text.lower())


def _bm25_top_indices(corpus: List[str], query: str, k: int) -> List[int]:
    """BM25 检索,返回按分数降序的语料下标。"""
    if not corpus:
        return []
    bm25 = BM25Okapi([tokenize(c) for c in corpus])
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return ranked[:k]


def rrf_fusion(results_list: List[List[Document]], k: int = 60) -> List[Document]:
    """RRF 融合多路召回结果。"""
    scores: dict = {}
    docs_map: dict = {}
    for results in results_list:
        for rank, doc in enumerate(results):
            key = doc.page_content
            docs_map[key] = doc
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [docs_map[key] for key, _ in ranked]


def retrieve_kb(
    kb_id: int,
    embeddings,
    query: str,
    chunk_items: List[dict],
    retrieval_type: str,
    top_k: int,
) -> List[Document]:
    """对单个知识库检索。

    :param chunk_items: 该知识库全部子块,格式 [{content, kb_id, document_id, parent_id}, ...]
        (用于混合检索的 BM25,并携带元数据以支持父子分块映射与引用链接)。
    """
    store = get_vector_store(kb_id, embeddings)
    vector_hits = store.similarity_search(query, k=top_k)

    if retrieval_type == "dense":
        return vector_hits

    # 混合检索:向量 + BM25 -> RRF 融合(BM25 命中携带与向量一致的元数据)
    corpus = [c["content"] for c in chunk_items]
    bm25_hits = [
        Document(
            page_content=chunk_items[i]["content"],
            metadata={
                "kb_id": chunk_items[i].get("kb_id"),
                "document_id": chunk_items[i].get("document_id"),
                "parent_id": chunk_items[i].get("parent_id"),
            },
        )
        for i in _bm25_top_indices(corpus, query, top_k)
    ]
    return rrf_fusion([vector_hits, bm25_hits])[:top_k]


def retrieve_multi_kb(
    kb_ids: List[int],
    embeddings,
    query: str,
    kb_chunks: dict[int, List[dict]],
    kb_retrieval_types: dict[int, str],
    top_k: int | None = None,
) -> List[Document]:
    """对多个知识库检索并合并结果(按原始相关度去重)。"""
    top_k = top_k or settings.retrieval_top_k
    merged: List[Document] = []
    for kb_id in kb_ids:
        chunks = kb_chunks.get(kb_id, [])
        rtype = kb_retrieval_types.get(kb_id, "hybrid")
        try:
            merged.extend(retrieve_kb(kb_id, embeddings, query, chunks, rtype, top_k))
        except Exception as e:
            logger.warning("检索失败 kb=%s: %s", kb_id, e)
    return merged[: settings.final_top_k * 2]
