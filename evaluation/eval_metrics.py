"""评估指标:检索召回率 + 回答忠实度(LLM-as-judge)。"""
from __future__ import annotations

from typing import List


def recall_at_k(gold_sources: List[str], retrieved_sources: List[str], k: int = 5) -> float:
    """检索召回率:检索结果前 k 个是否命中标准答案来源。

    返回 0.0 ~ 1.0;gold_sources 为空时返回 0.0。
    """
    if not gold_sources:
        return 0.0
    hits = len(set(gold_sources) & set(retrieved_sources[:k]))
    return hits / len(gold_sources)


def faithfulness_score(question: str, answer: str, context: str) -> str:
    """忠实度:用 LLM 判断回答是否忠实于上下文、未编造事实(LLM-as-judge)。

    返回 judge 的结论文本(如"忠实/不忠实 + 理由")。
    """
    from generation.llm import get_llm

    prompt = f"""请判断下面的回答是否完全基于给定上下文、没有编造事实。
只回答"忠实"或"不忠实",并给一句简短理由。

上下文:
{context}

问题:{question}
回答:{answer}

结论:"""
    return get_llm().invoke(prompt).content


def evaluate_item(question: str, gold_answer: str, gold_sources: List[str],
                  answer: str, retrieved_sources: List[str], context: str) -> dict:
    """对单条结果做综合评估,返回指标字典。"""
    return {
        "recall@5": recall_at_k(gold_sources, retrieved_sources),
        "faithfulness": faithfulness_score(question, answer, context),
    }
