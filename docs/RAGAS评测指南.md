# RAGAS 评测指南 — 企业知识问答系统

> 使用 [RAGAS](https://docs.ragas.io/) 框架对本系统的**检索**与**生成**链路做标准化评估。
> 指标全部基于大模型(LLM-as-judge)与语义相似度自动打分,无需人工标注。

---

## 1. 为什么用 RAGAS

本项目自带的 `evaluation/eval_metrics.py` 只有两个简易指标(recall@k + LLM 忠实度判断)。
RAGAS 提供业界标准化的 RAG 指标,且针对中文场景同样适用:

| 指标 | 衡量什么 | 需要的输入 |
|---|---|---|
| **Faithfulness(忠实度)** | 回答中的每句陈述是否都能由检索到的上下文支撑(不编造) | question, answer, contexts |
| **Answer Relevancy(答案相关性)** | 回答与问题的相关程度(是否答非所问) | question, answer |
| **Context Precision(上下文精确率)** | 检索结果中,真正相关的上下文是否排在前面 | question, contexts |
| **Context Recall(上下文召回率)** | 标准答案中的信息点是否都被检索到的上下文覆盖 | question, contexts, ground_truth |
| **Answer Correctness(答案正确性)** | 回答与标准答案在事实与语义上的一致性 | question, answer, ground_truth |

- **检索侧**:Context Precision / Context Recall(评估向量检索 + BM25 + RRF 的效果)
- **生成侧**:Faithfulness / Answer Relevancy / Answer Correctness(评估提示词与 LLM 输出质量)

---

## 2. 环境与依赖

```bash
uv add --group dev "ragas>=0.2.6,<0.3"
```

评测使用与线上完全相同的模型:

- **judge LLM(打分模型)**:通义 qwen-max(`app/rag/llm.py`)
- **embeddings**:通义 DashScope text-embedding(`app/rag/embeddings.py`)

> 注意:评测需要消耗 LLM API 额度(每个问题约 4~6 次 LLM 调用用于打分)。

---

## 3. 评测数据集

文件:`data/ragas_eval.json`

字段:

| 字段 | 说明 |
|---|---|
| `question` | 用户问题(取自三份测试文档的真实内容) |
| `gold_answer` | 标准答案(按文档原文编写,用于 Context Recall / Answer Correctness) |
| `gold_sources` | 期望命中的来源文档(辅助人工核对,不参与 RAGAS 打分) |

当前 16 条,覆盖三份文档:《员工手册》《产品说明-星云智能音箱》《常见问题 FAQ》,
包含数值类(天数/倍数/金额)、流程类(如何申请)、故障处理类(无法连接 Wi-Fi)等问题类型。

---

## 4. 运行评测

```bash
# 方式一:直接跑(自动准备评测知识库 + 文档解析 + 全链路评测)
uv run python evaluation/ragas_eval.py

# 方式二:指定数据集与输出
uv run python evaluation/ragas_eval.py \
    --dataset data/ragas_eval.json \
    --output docs/ragas_eval_result.json \
    --kb-name "评测知识库"
```

脚本内部流程:

1. **准备知识库**:查找/创建名为"评测知识库"的 KB,上传 `data/raw/` 下三份文档并同步解析(已存在则跳过,避免重复消耗额度);
2. **跑真实检索链路**:问题 → embedding → Milvus 向量召回 + BM25 关键词召回 → RRF 融合 → 子块映射回父块,得到 contexts;
3. **跑真实生成链路**:用与线上一致的提示词(`app/rag/prompts.py`)调用 qwen-max 生成回答;
4. **RAGAS 打分**:Faithfulness / ResponseRelevancy / ContextPrecision / ContextRecall / AnswerCorrectness;
5. **输出**:控制台表格 + `docs/ragas_eval_result.json`(每题的详细分数)。

---

## 5. 结果解读

| 分数区间 | Faithfulness | Answer Relevancy | Context Precision | Context Recall | Answer Correctness |
|---|---|---|---|---|---|
| 0.9 ~ 1.0 | 回答完全有据可依 | 高度切题 | 相关上下文全部靠前 | 上下文完整覆盖标准答案 | 与标准答案高度一致 |
| 0.7 ~ 0.9 | 基本忠实,少量推断 | 基本切题 | 大部分相关上下文靠前 | 覆盖大部分要点 | 基本一致 |
| < 0.7 | 存在编造/跑偏 | 答非所问 | 相关上下文靠后/混入噪音 | 关键信息缺失 | 偏差较大 |

**排查方向**:

- Context Recall 低 → 检索召回不足:调小 chunk_size、增大 top_k、检查父子分块映射;
- Context Precision 低 → 召回噪音多:调大 chunk_size、检查 RRF 权重、换 dense/hybrid;
- Faithfulness 低 → 提示词约束不足/上下文过短诱导补全:检查 `prompts.py` 与 final_top_k;
- Answer Correctness 低但 Faithfulness 高 → 检索到相关内容但答案与标准答案措辞差异大:属生成质量问题,可优化提示词。

---

## 6. 复现与扩展

- 加问题:往 `data/ragas_eval.json` 追加条目(保持字段完整);
- 换知识库:改 `--kb-name` 指向真实业务库,或把 `--kb-ids` 参数指向现有知识库;
- 换模型:修改 `.env` 的 `LLM_MODEL` / `EMBEDDING_MODEL` 后重跑,可对比不同模型效果。
