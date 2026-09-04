# RAG 检索原理

## 📋 概述

本文档介绍 RAG 系统的检索原理和实现。

---

## 🎯 检索流程

```
用户问题
    │
    ▼
┌─────────────────────────────────────────────┐
│            混合检索 (Hybrid Retrieval)       │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────┐      ┌─────────────┐      │
│  │ 稠密向量检索 │      │ 稀疏BM25检索│      │
│  │ (Dense)     │      │ (Sparse)    │      │
│  │             │      │             │      │
│  │ 语义相似度   │      │ 关键词匹配  │      │
│  └─────────────┘      └─────────────┘      │
│         │                    │              │
│         └────────┬───────────┘              │
│                  │                          │
│                  ▼                          │
│         ┌─────────────┐                    │
│         │  RRF 融合    │                    │
│         │  排序        │                    │
│         └─────────────┘                    │
│                  │                          │
│                  ▼                          │
│         ┌─────────────┐                    │
│         │ 父子分块映射 │                    │
│         └─────────────┘                    │
└─────────────────────────────────────────────┘
    │
    ▼
返回相关文档块
```

---

## 🔍 稠密向量检索 (Dense Retrieval)

### 原理

将文本转换为高维向量，通过向量相似度进行检索。

### 实现

```python
# 文本向量化
embedding = DashScopeEmbeddings.embed_query("什么是RAG?")

# Milvus 向量检索
results = milvus_client.search(
    collection_name="chunks",
    data=[embedding],
    limit=10,
    output_fields=["document_id", "content"]
)
```

### 特点

- ✅ 能理解语义相似性
- ✅ 对同义词、近义词友好
- ❌ 对精确关键词匹配较弱

---

## 📝 稀疏检索 (BM25)

### 原理

基于词频统计的传统检索算法，擅长关键词匹配。

### 实现

```python
from rank_bm25 import BM25Okapi

# 构建 BM25 索引
tokenized_corpus = [jieba.lcut(doc) for doc in documents]
bm25 = BM25Okapi(tokenized_corpus)

# 检索
query_tokens = jieba.lcut("RAG 检索增强生成")
scores = bm25.get_scores(query_tokens)
```

### 特点

- ✅ 精确关键词匹配
- ✅ 无需 GPU，速度快
- ❌ 无法理解语义

---

## 🔗 RRF 融合 (Reciprocal Rank Fusion)

### 原理

将多个检索结果按排名融合，综合各方法的优势。

### 公式

```
RRF_score(d) = Σ 1 / (k + rank_i(d))
```

其中 `k=60`（常数），`rank_i(d)` 是文档 `d` 在第 `i` 个检索器中的排名。

### 实现

```python
def reciprocal_rank_fusion(
    dense_results: List,
    sparse_results: List,
    k: int = 60
) -> List[Tuple]:
    fused_scores = {}
    
    for rank, doc in enumerate(dense_results):
        doc_id = doc["chunk_id"]
        fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1 / (k + rank + 1)
    
    for rank, doc in enumerate(sparse_results):
        doc_id = doc["chunk_id"]
        fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1 / (k + rank + 1)
    
    return sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
```

---

## 👨‍👦 父子分块 (Parent-Child Chunking)

### 原理

将文档分为父块和子块：
- **子块**：用于向量化和检索（较小，精度高）
- **父块**：用于返回给 LLM（较大，上下文完整）

### 分块策略

```
原始文档
    │
    ▼
┌─────────────────────────────────────┐
│ 父块 (Parent Chunk)                 │
│ 大小：2000 字符                      │
│                                     │
│  ┌──────┐ ┌──────┐ ┌──────┐       │
│  │子块1 │ │子块2 │ │子块3 │       │
│  │500字 │ │500字 │ │500字 │       │
│  └──────┘ └──────┘ └──────┘       │
└─────────────────────────────────────┘
```

### 检索流程

1. 用子块进行向量检索
2. 找到匹配的子块
3. 映射到对应的父块
4. 返回父块给 LLM

---

## 📊 多知识库检索

### 流程

```
用户选择知识库 [KB1, KB2, KB3]
    │
    ├── 检索 KB1 → 结果1
    ├── 检索 KB2 → 结果2
    └── 检索 KB3 → 结果3
    │
    ▼
合并所有结果
    │
    ▼
RRF 融合排序
    │
    ▼
返回 Top-K 结果
```

---

## ⚙️ 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| retrieval_type | hybrid | 检索类型：hybrid/dense |
| chunk_size | 500 | 子块大小 |
| chunk_overlap | 50 | 子块重叠 |
| parent_chunk_size | 2000 | 父块大小 |
| top_k | 5 | 返回结果数 |

---

## 📈 性能优化

### BM25 缓存

```python
# 缓存 BM25 索引，避免重复构建
_bm25_cache: dict = {}
_CACHE_MAX_SIZE = 50
```

### Embedding 缓存

```python
# 缓存向量化结果
_embedding_cache: dict = {}
_CACHE_MAX_SIZE = 10000
```

---

## 📚 相关文档

- [技术架构](./architecture.md)
- [父子分块](../features/parent-child-chunking.md)
- [性能优化](../optimization/performance.md)
