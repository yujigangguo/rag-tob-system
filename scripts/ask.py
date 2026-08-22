"""CLI 快速提问,验证端到端链路。

用法(在项目根目录执行):
    python scripts/ask.py "你的问题"
"""
from __future__ import annotations

import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中(支持从任意目录运行脚本)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from indexing.embed import get_embeddings
from indexing.vector_store import get_vector_store, load_chunks
from pipeline.rag_chain import RAGChain
from retrieval.hybrid_search import BM25Retriever


def main():
    if len(sys.argv) < 2:
        print('用法: python scripts/ask.py "你的问题"')
        return

    question = sys.argv[1]

    store = get_vector_store(get_embeddings())
    docs = load_chunks()
    bm25 = BM25Retriever(docs)

    chain = RAGChain(store, bm25)
    result = chain.ask(question)

    print("=" * 60)
    print(result["answer"])
    print("=" * 60)
    print("来源:", result["sources"])


if __name__ == "__main__":
    main()
