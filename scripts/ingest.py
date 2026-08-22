"""构建索引:data/raw 文档 -> 清洗 -> 切分 -> 向量化 -> 入库。

用法(在项目根目录执行):
    python scripts/ingest.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中(支持从任意目录运行脚本)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.loaders import load_directory
from ingestion.cleaner import clean_documents
from ingestion.chunker import split_documents
from indexing.vector_store import add_documents, save_chunks


def main():
    print("[1/4] 加载文档 ...")
    docs = load_directory()

    print(f"[2/4] 清洗文档 (加载到 {len(docs)} 段) ...")
    docs = clean_documents(docs)

    print("[3/4] 切分文档 ...")
    chunks = split_documents(docs)
    print(f"      切分后 {len(chunks)} 个 chunk")

    print("[4/4] 向量化并写入向量库 ...")
    add_documents(chunks)

    print("[5/5] 保存 chunk 文本(供 BM25 索引) ...")
    path = save_chunks(chunks)
    print(f"      已保存到 {path}")

    print("完成!向量库与 BM25 语料均已构建。")


if __name__ == "__main__":
    main()
