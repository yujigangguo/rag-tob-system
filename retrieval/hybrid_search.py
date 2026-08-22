"""混合检索:向量检索 + BM25 关键词检索 + RRF 融合。

单一向量检索对精确关键词(人名、型号、编号)不够敏感,
加上 BM25 后召回更全,再用 RRF 融合两路结果。
"""
from __future__ import annotations

import re
from typing import List

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from config.settings import settings


def tokenize(text: str) -> List[str]:
    """简单分词:中文按单字、英文按单词、数字保留。

    生产环境可替换为 jieba 分词以提升效果。
    """
    return re.findall(r"[\u4e00-\u9fff]|[a-zA-Z0-9]+", text.lower())


class BM25Retriever:
    """基于 rank_bm25 的关键词检索器。"""

    def __init__(self, documents: List[Document]):
        self.documents = documents
        self._bm25 = BM25Okapi([tokenize(d.page_content) for d in documents])

    def search(self, query: str, k: int = 20) -> List[Document]:
        """返回按 BM25 分数降序的前 k 个文档。"""
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [self.documents[i] for i in ranked[:k]]


def rrf_fusion(results_list: List[List[Document]], k: int = 60) -> List[Document]:
    """RRF(Reciprocal Rank Fusion)融合多路召回结果。

    :param results_list: 多路召回结果,每路已按相关度降序。
    :param k: RRF 常数,通常取 60。
    """
    scores: dict = {}
    docs_map: dict = {}
    for results in results_list:
        for rank, doc in enumerate(results):
            key = doc.page_content  # 用内容作去重键;有稳定 ID 时更佳
            docs_map[key] = doc
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [docs_map[key] for key, _ in ranked]


def hybrid_search(query: str, vector_store, bm25: BM25Retriever, k: int | None = None) -> List[Document]:
    """向量 + BM25 双路召回并 RRF 融合,返回前 k 个文档。"""
    k = k or settings.retrieval_top_k

    vector_hits = vector_store.similarity_search(query, k=k)
    bm25_hits = bm25.search(query, k=k)

    fused = rrf_fusion([vector_hits, bm25_hits])
    return fused[:k]
