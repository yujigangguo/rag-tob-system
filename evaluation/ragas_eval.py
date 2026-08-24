"""RAGAS 全链路评测:真实检索 + 生成 -> RAGAS 五指标打分。

用法:
    uv run python evaluation/ragas_eval.py
    uv run python evaluation/ragas_eval.py --dataset data/ragas_eval.json --output docs/ragas_eval_result.json --limit 16

输出:
    控制台指标汇总 + JSON(每题答案/上下文/各指标分 + 汇总)。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# 保证从项目根目录运行时可导入 app / evaluation
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ragas import EvaluationDataset, SingleTurnSample, evaluate  # noqa: E402
from ragas.embeddings import LangchainEmbeddingsWrapper  # noqa: E402
from ragas.llms import LangchainLLMWrapper  # noqa: E402
from ragas.metrics import (  # noqa: E402
    LLMContextPrecisionWithoutReference,
    LLMContextRecall,
    AnswerCorrectness,
    Faithfulness,
    ResponseRelevancy,
)
from ragas.run_config import RunConfig  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.rag.embeddings import get_embeddings  # noqa: E402
from app.rag.llm import get_llm  # noqa: E402
from evaluation.pipeline import (  # noqa: E402
    ensure_docs_parsed,
    generate_answer,
    get_or_create_eval_kb,
    load_eval_dataset,
    retrieve_contexts,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="RAGAS 评测")
    p.add_argument("--dataset", default="data/ragas_eval.json", help="评测集 JSON")
    p.add_argument("--output", default="docs/ragas_eval_result.json", help="结果输出 JSON")
    p.add_argument("--kb-name", default=None, help="评测知识库名称(默认自动创建/复用)")
    p.add_argument("--limit", type=int, default=None, help="只评测前 N 条")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    db = SessionLocal()
    try:
        print("=== 1. 准备评测知识库 ===")
        kb = get_or_create_eval_kb(db)
        print(f"评测知识库: id={kb.id} name={kb.name} 检索方式={kb.retrieval_type}")
        ensure_docs_parsed(db, kb.id)

        items = load_eval_dataset(args.dataset)
        if args.limit:
            items = items[: args.limit]
        print(f"=== 2. 跑检索 + 生成链路({len(items)} 条)===")

        samples = []
        per_item = []
        t0 = time.time()
        for idx, it in enumerate(items, 1):
            q = it["question"]
            contexts = retrieve_contexts(db, kb.id, q)
            answer = generate_answer(q, contexts)
            samples.append(
                SingleTurnSample(
                    user_input=q,
                    response=answer,
                    retrieved_contexts=contexts,
                    reference=it["gold_answer"],
                )
            )
            per_item.append(
                {
                    "question": q,
                    "gold_answer": it["gold_answer"],
                    "answer": answer,
                    "contexts": contexts,
                }
            )
            print(f"  [{idx}/{len(items)}] 完成: {q[:30]}... 上下文 {len(contexts)} 段")
        print(f"检索+生成耗时: {time.time() - t0:.1f}s")

        print("=== 3. RAGAS 打分 ===")
        llm = get_llm(streaming=False)
        embeddings = get_embeddings()
        evaluator_llm = LangchainLLMWrapper(llm)
        evaluator_emb = LangchainEmbeddingsWrapper(embeddings)

        metrics = [
            Faithfulness(llm=evaluator_llm),
            ResponseRelevancy(llm=evaluator_llm, embeddings=evaluator_emb),
            LLMContextPrecisionWithoutReference(llm=evaluator_llm),
            LLMContextRecall(llm=evaluator_llm),
            AnswerCorrectness(llm=evaluator_llm, embeddings=evaluator_emb),
        ]
        dataset = EvaluationDataset(samples=samples)
        result = evaluate(
            dataset,
            metrics=metrics,
            llm=evaluator_llm,
            embeddings=evaluator_emb,
            run_config=RunConfig(timeout=180, max_workers=4),
            raise_exceptions=True,
        )

        df = result.to_pandas()
        metric_names = [m.name for m in metrics]
        aggregate = {
            name: round(float(df[name].mean()), 4) if name in df.columns else None
            for name in metric_names
        }

        print("\n=== 汇总 ===")
        for name, score in aggregate.items():
            print(f"  {name:<28} {score}")
        print(f"  平均分                          {sum(v for v in aggregate.values() if v is not None) / len([v for v in aggregate.values() if v is not None]):.4f}")

        # 每题分数并入结果
        for i, row in enumerate(per_item):
            for name in metric_names:
                val = df.iloc[i][name] if name in df.columns and i < len(df) else None
                row[name] = round(float(val), 4) if val is not None else None

        out = {
            "evaluated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "kb_id": kb.id,
            "kb_name": kb.name,
            "llm_model": "qwen-max",
            "retrieval_type": kb.retrieval_type,
            "metrics": metric_names,
            "aggregate": aggregate,
            "items": per_item,
        }
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存: {args.output}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
