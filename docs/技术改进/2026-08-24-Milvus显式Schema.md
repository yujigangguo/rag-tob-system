# 技术改进:Milvus 显式 Schema(修复 parent_id 字段缺失/插入失败)

> 日期:2026-08-24
> 涉及:向量库写入层 `app/rag/vector_store.py`
> 对应问题:改版后新增的 `parent_id` 字段在旧 collection 中不可见;上传解析报 `unexpected field 'parent_id'`

---

## 1. 变更概述

Milvus 的 collection schema **建库时固定、不可事后加字段**。旧代码创建的 collection 没有 `parent_id`
字段,且 `enable_dynamic_field=False`,导致:

- 新代码写入带 `parent_id` 的 metadata 时,本地(静默丢弃)与容器(直接报错)行为不一致,上传"时好时坏";
- 检索结果中永远拿不到 `parent_id`,父子分块映射退化。

本次将建库方式改为**显式声明 schema**,固定 4 个 metadata 字段为 INT64,不依赖"首次插入隐式推断"。

---

## 2. 新旧功能对比

| 场景 | 旧行为 | 新行为 |
|------|--------|--------|
| 新建 collection 的字段 | 由首次插入的 metadata **隐式推断**,可能缺字段/类型漂移 | **显式固定**:text/pk/vector/kb_id/document_id/parent_id/chunk_index |
| 新库是否含 `parent_id` | 取决于首次插入是否带该 key(碰运气) | **必然包含**,类型固定 INT64 |
| 向旧库写入新字段 metadata | 本地静默丢弃 / 容器直接报错(不一致) | 行为一致:未知字段被跳过(不报错);重建后字段完整 |
| 排查难度 | "时好时坏",容器与本地表现不同 | 结构确定,可预期 |

---

## 3. 代码改动点

| 文件 | 改动 |
|------|------|
| `app/rag/vector_store.py` | 新增 `MILVUS_METADATA_FIELDS` 常量与 `_metadata_schema()`(每次调用新建字典,避免 langchain-milvus 内部 pop 修改共享对象);`get_vector_store` 传入 `metadata_schema` |

---

## 4. 数据与接口变化

无接口变化;Milvus 新 collection 的 schema 固定为:

| 字段 | 类型 |
|------|------|
| text | VARCHAR |
| pk | INT64(主键,自动) |
| vector | FLOAT_VECTOR(1024) |
| kb_id / document_id / parent_id / chunk_index | INT64 |

---

## 5. 影响与注意事项

- **存量 collection**:旧库结构不变(不能原地加字段),需删库重建/重新上传后才有完整字段——已在部署说明中提示;
- **容器与本地**:依赖统一由 `uv.lock` 锁定,重建镜像后行为一致;
- **新知识库**:从创建起即具备完整 schema,无需额外处理。

---

## 6. 验证情况

- 探针实测:通过应用代码路径新建临时 collection,`describe_collection` 返回完整 7 字段,插入带 `parent_id` 的数据成功并可查询;
- 全量 pytest 通过(解析入库用例覆盖该链路)。
