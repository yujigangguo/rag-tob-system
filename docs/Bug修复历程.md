# Bug 修复历程 — 企业知识问答系统

> 本阶段(2026-08-24)共排查并修复 **7 个问题**,涵盖向量库 schema 不一致、数据库外键、上传链路、权限状态、引用数据流等。
> 每个问题按「现象 → 根因 → 修复 → 验证」记录,文末附共性总结与改进建议。

---

## 1. Milvus 看不到新字段 + 上传解析失败

**现象**
- 改版后新增的 `parent_id` 字段在 Milvus(Attu / describe_collection)里看不到;
- 随后上传文档解析直接失败:`DataNotMatchException: Attempt to insert an unexpected field 'parent_id' to collection without enabling dynamic field`;
- 表现"时好时坏":同一代码同一数据,某些上传成功、某些失败。

**根因**
- Milvus 的 collection schema **建库时固定,不能事后加字段**;
- 现有 collection(`kb_1/2/3`)由**旧代码**创建,只有 `text/pk/vector/kb_id/document_id/chunk_index` 六个字段,且 `enable_dynamic_field=False`;
- langchain-milvus 对"schema 里不存在的 metadata 字段":本机 `.venv` 版本**静默丢弃**,Docker 容器内版本**直接报错**——行为不一致导致"时好时坏";
- 后端实际跑在 Docker 容器(镜像构建时 `COPY` 固化代码),与本地 `.venv` 依赖版本不一致。

**修复**
- `app/rag/vector_store.py`:建库时**显式声明 schema**(`metadata_schema` 固定 kb_id / document_id / parent_id / chunk_index 为 INT64),不再依赖"首次插入 metadata 隐式推断";
- 重建 Docker 镜像(`docker compose up -d --build`),让容器与本地依赖一致。

**验证**:临时 collection 实测——显式 schema 下新建 collection 必含 `parent_id`,插入带 parent_id 的数据成功、可查询。

---

## 2. 知识库列表"文档数"永远是 0

**现象**
- 上传文档后,知识库列表页仍显示"文档 0 个"。

**根因**
- 初始提交起就存在的 bug:`delete_document` 里有 `kb.doc_count -= 1`,但 `upload_document` **从未 `+= 1`**——计数只减不加。

**修复**
- `app/services/document_service.py`:`upload_document` 创建文档记录时补 `kb.doc_count += 1`;
- 存量数据用 SQL 回填:`UPDATE knowledge_bases SET doc_count = (SELECT COUNT(*) FROM documents ...)`。

**验证**:回填后各知识库 doc_count 与 documents 表实际行数一致;上传/删除后计数正确增减。

---

## 3. 上传大文件报"网络错误"

**现象**
- 上传超过一定大小的 PDF,前端提示"网络错误",无具体原因。

**根因**
- 前端 nginx(`frontend/nginx.conf`)**未配置 `client_max_body_size`**,默认上限 **1MB**;
- 超限时 nginx 直接返回 **413**(HTML 页面,无 JSON `detail`),axios 拦截器取不到错误信息 → 走兜底分支弹"网络错误";
- 请求根本没到后端,与解析能力无关。

**修复**
- `frontend/nginx.conf` 加 `client_max_body_size 10m;`(曾设 100MB,按需求改为 10MB);
- `config/settings.py` 新增 `max_upload_size_mb = 10`;`upload_document` 增加大小校验(Content-Length 快速预检 + 流式分块计数兜底),超限返回明确提示"文件过大:最大支持 10MB",并清理已写残文件;
- 前端上传弹窗提示补充"单个文件最大 10MB";`.env.example` 增加 `MAX_UPLOAD_SIZE_MB`。

**验证**:>10MB 上传返回 413 明确报错;≤10MB 正常。

---

## 4. 部门管理员"创建不了"知识库(假 bug → 旧登录态)

**现象**
- 部门管理员(dept_admin)登录后看不到"创建知识库"按钮,或创建被拦。

**排查过程(逐层排除)**
1. 后端接口实测:以 `product_admin` 直接调创建接口 → **200 成功**,后端逻辑无 bug;
2. 前端代码检查:创建弹窗预选本部门、提交带 `department_id`,逻辑正确;
3. 探针验证:运行中的前后端容器均为新代码(`/api/departments` 存在、前端 chunk 含"所属部门");
4. **结论**:浏览器 localStorage 里是**改版前登录的旧会话**——旧登录只存了 username/token,没有 role/departmentId;新前端读不到 → 把部门管理员当成 employee → 创建按钮被隐藏。

**修复(加固,防复发)**
- `app/api/auth.py`:`/auth/me` 增加 `department_name`;
- 前端 `main.ts` 启动时调 `/auth/me`,用**后端真实角色/部门**覆盖本地 localStorage(`auth store.syncUser`);
- 用户侧:重新登录(或清 localStorage)即可。

**验证**:localStorage 缺失角色信息时,页面加载后自动修正权限展示。

---

## 5. 删除知识库/文档报外键冲突

**现象**
- 测试中删除知识库或文档报:`IntegrityError: Cannot delete or update a parent row ... FOREIGN KEY (parent_id) REFERENCES chunks (id)`。

**根因**
- 父子分块后 `chunks` 表有**自引用外键**(`parent_id → id`);
- `delete_kb` / `delete_document` 用一条语句整批删除,先删父块 → 子块还引用着 → 违反约束;
- 生产库未暴露的原因:生产 `chunks` 表是旧结构,**根本没有这条外键**(`create_all` 不会给已存在表加约束);测试库每次全新创建,带完整外键,问题暴露。

**修复**
- `app/services/document_service.py`、`app/services/kb_service.py`:删除时**先删子块(`parent_id IS NOT NULL`),再删父块**。

**验证**:全量 pytest 通过;带外键的全新测试库上删除正常。

---

## 6. 混合检索 BM25 命中丢失元数据(隐藏 bug)

**现象**
- 做引用链接功能时发现:`citations` 映射的 kb_id / document_id / chunk_id 全为 null;
- 进一步排查发现更严重的问题:混合检索模式下,**BM25 命中的子块从未被映射回父块**(父子分块功能对 BM25 命中失效)。

**根因**
- `app/rag/retrieval.py` 中 BM25 构造的 `Document` **只有 page_content,没有 metadata**;
- RRF 融合时按文本去重,BM25 文档(无元数据)可能覆盖同内容的向量文档 → `_map_to_parents` 读不到 parent_id → 走"旧数据回退"分支。

**修复**
- BM25 语料由纯文本改为携带元数据:调用方(`chat_service` / `evaluation/pipeline.py`)传 `{content, kb_id, document_id, parent_id}`,BM25 命中构造带相同元数据的 Document。

**验证**:引用映射恢复完整(kb_id=6、document_id/chunk_id 有值);混合检索命中的子块能正确映射回父块。

---

## 7. 历史对话引用链接不可点

**现象**
- 查看历史对话时,回答里的 [1][2] 显示为链接样式,但点击无反应;当前会话刷新页面后同样失效。

**根因(数据未持久化)**
- citations 映射只通过 SSE 在**生成时一次性下发**,仅存于前端**内存**消息对象;
- 后端 `ChatMessage` 未保存 citations,`listMessages` 返回的消息里没有该字段;
- 历史消息从接口加载时无映射 → `[N]` 渲染成"无功能的链接"。

**修复**
- `app/models/chat.py`:`ChatMessage` 增加 `citations` JSON 列;
- `app/services/chat_service.py`:`stream_answer` 保存助手消息时把 citations 一并落库;
- `app/schemas/chat.py`:`ChatMessageOut` 增加 `citations` 返回;
- 前端类型补充 `ChatMessage.citations`,历史消息加载后自动恢复可点击引用;
- `scripts/init_rbac.py` 增加幂等迁移列。

**验证**:生成 → 通过历史消息接口能取回 citations(实测 `[{index, kb_id, chunk_id, document_id}...]`);pytest 新增断言覆盖。

---

## 共性根因总结

这 7 个问题可以归纳为 5 类根因模式:

| 模式 | 涉及问题 | 本质 |
|---|---|---|
| **Milvus schema 与代码不一致** | #1 | Milvus 建库后不能改 schema;旧库结构跟不上新代码 → 显式 schema + 重建 |
| **数据库 schema 与模型不一致** | #5 | `create_all` 只建新表、不给已存在表加列/约束;新旧库结构分裂 → 幂等迁移脚本 |
| **运行环境与开发环境不一致** | #1、#4 | Docker 镜像固化代码/依赖;`.venv` 与容器行为不同 → 重建镜像 + 统一依赖锁 |
| **前端本地状态与后端不一致** | #4 | localStorage 旧登录态误导权限展示 → 启动时从后端同步(/auth/me) |
| **数据流中状态丢失** | #6、#7 | BM25 丢失元数据;引用映射未持久化 → 让关键数据随链路/落库流转 |

## 改进建议

1. **引入正式迁移机制**:目前靠 `scripts/init_rbac.py` 幂等脚本 + 手动 SQL;建议后续接 Alembic,避免"生产库结构落后于模型"这类问题再次发生;
2. **统一环境**:CI/本地用同一份 `uv.lock`,镜像构建锁定依赖,避免容器/本地行为分叉;
3. **测试覆盖**:本次新增权限矩阵、公开库、引用持久化等测试(全量 17 个通过);建议把"删除带父子结构的库/文档"等外键场景纳入回归用例;
4. **前端状态自愈**:任何"本地缓存可能过期"的用户态(角色、部门),都应以接口为准、启动时同步。

---

*相关文件:详见各问题"修复"条目;功能演进(三级权限、公开知识库、引用链接、RAGAS 评测)见 `docs/项目演示文档.md` 与 `docs/RAGAS评测报告.md`。*
