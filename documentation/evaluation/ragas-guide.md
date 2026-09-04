# RAGAS 评测指南

## 📋 概述

RAGAS (Retrieval Augmented Generation Assessment) 是一个用于评测 RAG 系统质量的框架。

---

## 🎯 评测指标

| 指标 | 说明 | 范围 |
|------|------|------|
| Faithfulness | 回答是否忠实于检索到的上下文 | 0-1 |
| Answer Relevancy | 回答与问题的相关性 | 0-1 |
| Context Precision | 检索上下文的精确度 | 0-1 |
| Context Recall | 检索上下文的召回率 | 0-1 |

---

## 🔧 使用方法

### 安装

```bash
uv add ragas
```

### 准备评测数据

```python
eval_data = [
    {
        "question": "什么是 RAG？",
        "ground_truth": "RAG 是检索增强生成技术",
        "answer": "RAG（检索增强生成）是一种结合信息检索和大语言模型的技术...",
        "contexts": ["RAG 是 Retrieval Augmented Generation 的缩写..."]
    }
]
```

### 执行评测

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

result = evaluate(
    dataset=eval_dataset,
    metrics=[faithfulness, answer_relevancy],
)
print(result)
```

---

## 📊 评测结果解读

| 分数范围 | 评价 |
|----------|------|
| 0.9 - 1.0 | 优秀 |
| 0.7 - 0.9 | 良好 |
| 0.5 - 0.7 | 一般 |
| 0.0 - 0.5 | 需改进 |

---

## 📚 相关文档

- [评测报告](./ragas-report.md)
- [RAG 检索原理](../technical/rag-retrieval.md)
