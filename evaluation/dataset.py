"""评测集:问题 + 标准答案 + 期望命中的来源。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class EvalItem:
    """单条评测样本。"""
    question: str
    gold_answer: str
    gold_sources: List[str] = field(default_factory=list)


# 示例评测集 —— 请替换成你自己的真实问题(阶段 0 准备的样例)
SAMPLE_DATASET: List[EvalItem] = [
    EvalItem(
        question="示例:公司的年假政策是什么?",
        gold_answer="示例:员工每年享有 X 天带薪年假。",
        gold_sources=[],
    ),
]


def load_dataset(path: str | None = None) -> List[EvalItem]:
    """从 JSON 文件加载评测集,字段:question / gold_answer / gold_sources。

    不传 path 时返回内置示例评测集。
    """
    import json

    if path is None:
        return SAMPLE_DATASET
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [EvalItem(**item) for item in data]
