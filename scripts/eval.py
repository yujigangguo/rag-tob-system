"""RAG 检索命中率评估。

对评测集中的每个问题跑检索(稠密/混合),检查 top-k 召回的文档块
是否命中标准答案关键词,输出 Recall@k 命中率。

用法:
    uv run python scripts/eval.py --kb-id 1 --dataset data/eval.json --top-k 5

评测集 JSON 格式:
    [
      {"question": "年假有几天?", "keywords": ["5 天", "10 天", "15 天"]},
      {"question": "加班费怎么算?", "keywords": ["1.5 倍", "2 倍", "3 倍"]}
    ]

命中判定:召回文本中包含任一 keyword 即视为命中。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Chunk, KnowledgeBase
from app.rag.embeddings import get_embeddings
from app.rag.retrieval import retrieve_kb


def load_dataset(path: str) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def evaluate(kb_id: int, dataset: list[dict], top_k: int) -> float:
    """评估单个知识库的检索命中率,返回 recall 值。"""
    db = SessionLocal()
    try:
        kb = db.get(KnowledgeBase, kb_id)
        if kb is None:
            print(f"[错误] 知识库 {kb_id} 不存在")
            return 0.0

        chunks = list(db.scalars(select(Chunk.content).where(Chunk.kb_id == kb_id)).all())
        if not chunks:
            print(f"[错误] 知识库「{kb.name}」没有文档块,请先上传文档并解析")
            return 0.0

        embeddings = get_embeddings()
        print(f"知识库: {kb.name} | 检索方式: {kb.retrieval_type} | chunk 数: {len(chunks)} | top-k: {top_k}\n")

        hit = 0
        total = len(dataset)
        for i, item in enumerate(dataset, 1):
            question = item["question"]
            keywords = item.get("keywords", [])
            docs = retrieve_kb(kb_id, embeddings, question, chunks, kb.retrieval_type, top_k)
            retrieved_text = "\n".join(d.page_content for d in docs)
            matched = [kw for kw in keywords if kw in retrieved_text]
            ok = len(matched) > 0
            hit += 1 if ok else 0
            print(f"[{'√' if ok else '×'}] {question}")
            if keywords:
                print(f"    命中 {len(matched)}/{len(keywords)}: {matched if matched else '无'}")
            else:
                print("    (未配置关键词,不判定)")

        recall = hit / total if total else 0.0
        print(f"\n{'=' * 52}")
        print(f"Recall@{top_k} = {hit}/{total} = {recall:.1%}")
        return recall
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="RAG 检索命中率评估")
    parser.add_argument("--kb-id", type=int, required=True, help="知识库 id")
    parser.add_argument("--dataset", default="data/eval.json", help="评测集 JSON 路径")
    parser.add_argument("--top-k", type=int, default=5, help="召回数量")
    args = parser.parse_args()
    evaluate(args.kb_id, load_dataset(args.dataset), args.top_k)


if __name__ == "__main__":
    main()
