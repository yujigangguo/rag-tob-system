"""RAG 主链路编排:检索(混合+重排) -> 拼 prompt -> 生成。"""
from __future__ import annotations

from typing import List

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage

from config.settings import settings
from generation.llm import get_llm
from generation.prompt import RAG_SYSTEM_PROMPT, RAG_USER_PROMPT
from retrieval.hybrid_search import BM25Retriever, hybrid_search
from retrieval.reranker import rerank


class RAGChain:
    """端到端 RAG 问答链。"""

    def __init__(self, vector_store, bm25: BM25Retriever):
        self.vector_store = vector_store
        self.bm25 = bm25
        self.llm = get_llm()

    def retrieve(self, question: str) -> List[Document]:
        """召回 + 重排,返回最终交给 LLM 的上下文文档。"""
        hits = hybrid_search(question, self.vector_store, self.bm25)
        return rerank(question, hits, settings.final_top_k)

    def _build_context(self, docs: List[Document]) -> str:
        """把文档拼成带编号和来源的上下文字符串。"""
        parts = []
        for i, doc in enumerate(docs, 1):
            src = doc.metadata.get("source", "未知来源")
            parts.append(f"[{i}] {doc.page_content} (来源: {src})")
        return "\n\n".join(parts)

    def ask(self, question: str) -> dict:
        """回答问题,返回 {answer, sources}。"""
        docs = self.retrieve(question)
        context = self._build_context(docs)

        messages = [
            SystemMessage(content=RAG_SYSTEM_PROMPT),
            HumanMessage(content=RAG_USER_PROMPT.format(context=context, question=question)),
        ]
        answer = self.llm.invoke(messages).content

        sources = [doc.metadata.get("source", "未知来源") for doc in docs]
        return {"answer": answer, "sources": sources}
