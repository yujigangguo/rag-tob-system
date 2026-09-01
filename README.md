# 企业内容知识问答系统

基于 **RAG(检索增强生成)** 的全栈知识问答系统:用户上传企业文档到知识库,系统切分、向量化存入 Milvus,问答时检索相关上下文,由通义千问 qwen-max 流式生成回答并标注来源。

> 📘 连接信息、账号密码、部署与排查见 [`docs/使用说明.md`](docs/使用说明.md);接口文档见 [`docs/API.md`](docs/API.md)。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3 + TypeScript + Element Plus + Vite + Pinia |
| 后端 | FastAPI + SQLAlchemy + PyMySQL + PyJWT |
| 向量库 | Milvus(每知识库一个 collection) |
| 关系库 | MySQL 8.0(用户/知识库/文档/会话/消息) |
| 缓存 | Redis(验证码/会话缓存) |
| 大模型 | 通义千问 qwen-max(流式)+ text-embedding(向量化) |
| 测试/评测 | pytest(17 项)+ RAGAS 0.2(evaluation/) |

## 目录结构

```
rag-system/
├── backend 相关(项目根)
│   ├── app/                # FastAPI 应用
│   │   ├── main.py         # 入口(异常处理/限频/健康检查)
│   │   ├── database.py     # SQLAlchemy(连接池优化)
│   │   ├── security.py     # JWT / 密码 / 验证码(Redis)
│   │   ├── redis_client.py # Redis 客户端
│   │   ├── rbac.py         # 角色权限控制
│   │   ├── models/         # ORM 模型
│   │   ├── schemas/        # Pydantic
│   │   ├── api/            # 路由(含管理后台)
│   │   ├── services/       # 业务逻辑
│   │   └── rag/            # RAG 引擎(解析/向量/检索/生成)
│   ├── config/settings.py  # 配置
│   ├── alembic/            # 数据库迁移
│   ├── scripts/            # 启动脚本/备份脚本
│   └── tests/              # pytest 测试
├── frontend/               # Vue3 前端
│   └── src/
│       ├── views/          # 登录/注册/对话/知识库管理/详情
│       └── views/admin/    # 管理后台(用户/部门/权限)
├── data/                   # 上传文件、测试文档、演示数据、评测集
├── evaluation/             # RAGAS 评测(管线 + 入口)
├── docs/                   # 文档(API/使用说明/优化记录)
├── docker-compose.yml      # Milvus + MySQL + Redis + 后端 + 前端
├── .env.example            # 配置模板
└── pyproject.toml          # 后端依赖(uv)
```

## 功能特性

### 核心功能

- **用户认证**:注册 / 登录,图形验证码(Redis 存储) + JWT,密码 bcrypt 哈希
- **三级角色权限**:`super_admin`(系统管理员,所有部门)/ `dept_admin`(部门管理员,本部门)/ `employee`(员工,只读 + 问答);知识库按**部门隔离**,支持**全公司可见的公开知识库**(仅超管可建可管)
- **第一个用户自动超级管理员**:注册时自动检测,首个用户成为 super_admin
- **多知识库**:按部门共享,支持稠密/混合检索,自定义切块参数(含父块大小)
- **文档解析**:PDF / PPT / Markdown / TXT / 图片(图片暂不 OCR),后台异步解析 + 真实进度条,**父子分块**(子块检索、父块作上下文)向量化入 Milvus;上传大小上限 10MB(可配)
- **文档块管理**:预览、编辑(自动重向量化)、删除(仅管理员)
- **智能问答**:多知识库联合检索、流式输出、历史多轮对话、参数可调(温度/TopP/最大token/历史轮数)
- **对话重新生成**:删除最后一条助手消息,重新生成回答
- **引用溯源**:回答标注 [1][2] 来源编号,**可点击跳转到知识库对应文档块并高亮**;历史消息记录"本次检索的知识库来源"与引用映射,便于追溯与评测
- **RAGAS 评测**:内置 `evaluation/ragas_eval.py`,一键跑 Faithfulness / Relevancy / Context Precision / Context Recall / Correctness 五指标

### 管理后台(超级管理员)

- **用户管理**:用户列表(分页/搜索/筛选)、编辑、删除、分配角色、分配部门、禁用/启用
- **部门管理**:部门列表、创建、编辑、删除
- **权限管理**:角色列表、权限矩阵可视化
- **系统配置**:界面化修改 LLM 参数、检索参数、验证码开关
- **审计日志**:记录关键操作(删用户、改权限、删知识库等)
- **仪表盘**:用户总数、知识库总数、文档总量、对话总量统计

### 安全特性

- **接口限频**:登录 5次/分钟,注册 3次/分钟(防暴力破解)
- **全局异常处理**:统一错误响应格式,记录详细日志
- **用户账号禁用**:管理员可禁用/启用用户,禁用后无法登录
- **密码管理**:用户修改密码 + 管理员重置密码

### 性能优化

- **Redis 缓存**:验证码存储(重启不丢失,多实例共享)
- **BM25 索引缓存**:LRU 缓存,避免每次检索重建索引
- **数据库连接池**:pool_size=20, max_overflow=10,自动检测连接有效性

### 运维特性

- **Alembic 数据库迁移**:版本化迁移,支持增量更新
- **深度健康检查**:`/health/deep` 检查 MySQL/Milvus/Redis 连接状态
- **日志持久化**:挂载日志目录,日志轮转(10MB/文件,保留5个)
- **数据库自动备份**:定时备份脚本,保留7天

---

## 快速开始

### 方式 A:Docker 一键部署(推荐)

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env,填入 LLM_API_KEY 和 EMBEDDING_API_KEY

# 2. 启动所有服务
docker compose up -d --build

# 3. (可选)数据库迁移
RUN_MIGRATIONS=true docker compose up -d
```

**访问地址:**
- 前端:`http://localhost:8080`
- 后端文档:`http://localhost:8000/docs`
- 管理后台:`http://localhost:8080/admin`(需超级管理员登录)

### 方式 B:本地开发(前后端分离)

```bash
# 1. 起基础设施(MySQL + Milvus + Redis)
docker compose up -d mysql milvus redis

# 2. 后端(uv)
uv sync
cp .env.example .env          # 填 LLM_API_KEY 与 EMBEDDING_API_KEY
uv run uvicorn app.main:app --reload --port 8000

# 3. 前端(Vite,已代理 /api)
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

### 运行测试

```bash
uv run pytest                 # 17 项测试(问答测试需配置 LLM_API_KEY)
```

### RAGAS 评测

```bash
uv run python evaluation/ragas_eval.py    # 评测集 data/ragas_eval.json,详见 docs/RAGAS评测指南.md
```

---

## 关键配置(.env)

| 配置 | 说明 | 默认值 |
|------|------|--------|
| `LLM_API_KEY` | 通义 DashScope API Key(qwen-max) | - |
| `EMBEDDING_API_KEY` | 通义 embedding API Key(可与上面相同) | - |
| `DB_*` | MySQL 连接(docker-compose 默认 `rag_user` / `rag_db`) | - |
| `MILVUS_URI` | Milvus 地址 | `http://localhost:19530` |
| `REDIS_URL` | Redis 地址 | `redis://:1234@redis:6379/0` |
| `SECRET_KEY` | JWT 签名密钥,生产务必修改 | `change-me-in-production-please` |
| `DEFAULT_HISTORY_ROUNDS` | 默认历史对话轮数 | `5` |
| `MAX_UPLOAD_SIZE_MB` | 单文件上传上限(需与 nginx `client_max_body_size` 一致) | `10` |
| `RUN_MIGRATIONS` | Docker 启动时是否运行数据库迁移 | `false` |
| `AUTO_CREATE_TABLES` | 启动时是否自动建表(开发用) | `true` |

---

## 主要接口(均需 Bearer Token,前缀 `/api`)

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/auth/captcha` | 获取图形验证码 |
| POST | `/api/auth/register` | 注册(首个用户自动成为超级管理员) |
| POST | `/api/auth/login` | 登录(返回角色/部门) |
| GET | `/api/auth/me` | 当前用户信息(角色/部门/昵称/头像) |
| POST | `/api/auth/change-password` | 修改密码 |
| PUT | `/api/auth/profile` | 更新个人信息(昵称/邮箱/头像) |

### 知识库接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/departments` | 部门列表 |
| POST | `/api/knowledge-bases` | 创建知识库(仅管理员,含 `department_id` / `is_public`) |
| GET | `/api/knowledge-bases` | 知识库列表(部门可见 + 公开库) |
| PUT/DELETE | `/api/knowledge-bases/{id}` | 更新/删除(仅管理员) |
| POST | `/api/knowledge-bases/{id}/documents` | 上传文档(仅管理员,≤10MB,异步解析) |
| GET | `/api/knowledge-bases/{id}/documents/{doc_id}/progress` | 查询文档解析进度 |
| GET/PUT/DELETE | `/api/chunks/{id}` | 文档块查看/编辑/删除(编辑删除仅管理员) |

### 对话接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat/stream` | 流式问答(SSE,含引用映射 citations) |
| POST | `/api/chat/regenerate` | 重新生成最后一条回答 |
| DELETE | `/api/chat/messages/{id}` | 删除消息及后续消息 |
| GET/POST/PUT/DELETE | `/api/chat/sessions` | 会话管理 |
| GET | `/api/chat/sessions/{id}/messages` | 会话消息(含 citations / kb_ids) |

### 管理后台接口(需超级管理员)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/users` | 用户列表(分页/搜索/筛选) |
| GET/PUT | `/api/admin/users/{id}` | 用户详情/更新 |
| DELETE | `/api/admin/users/{id}` | 删除用户 |
| PUT | `/api/admin/users/{id}/role` | 分配角色 |
| PUT | `/api/admin/users/{id}/department` | 分配部门 |
| PUT | `/api/admin/users/{id}/status` | 禁用/启用用户 |
| POST | `/api/admin/users/{id}/reset-password` | 重置密码 |
| GET/POST/PUT/DELETE | `/api/admin/departments` | 部门管理 |
| GET | `/api/admin/roles` | 角色列表 |
| GET | `/api/admin/permissions` | 权限配置 |
| GET | `/api/admin/audit-logs` | 审计日志 |
| GET/PUT | `/api/admin/configs` | 系统配置 |
| GET | `/api/admin/dashboard` | 仪表盘统计 |

### 系统接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 基础健康检查 |
| GET | `/health/deep` | 深度健康检查(检查 MySQL/Milvus/Redis) |

---

## Docker 一键部署

一键启动 MySQL + Redis + Milvus + 后端 + 前端(nginx 托管并反向代理 `/api`,支持 SSE):

```bash
# 先在 .env 填好 LLM_API_KEY / EMBEDDING_API_KEY
docker compose up -d --build
```

**服务架构:**

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| 前端 | rag-frontend | 8080:80 | Vue3 + Nginx 反向代理 |
| 后端 | rag-backend | 8000:8000 | FastAPI + uvicorn |
| MySQL | rag-mysql | 3306:3306 | 用户/部门/知识库数据 |
| Redis | milvus-redis | 6379:6379 | 验证码/会话缓存 |
| Milvus | milvus-standalone | 19530:19530 | 向量数据库 |

**常用命令:**

```bash
docker compose up -d --build   # 启动
docker compose down            # 停止
docker compose down -v         # 停止并清空 MySQL 数据
docker compose logs -f backend # 查看后端日志
```

> 说明:Milvus 已纳入 compose,后端通过服务名 `milvus:19530` 访问;Redis 通过 `redis:6379` 访问;数据卷沿用本机 `E:/milvus_redis/volumes`(`.env` 的 `MILVUS_VOLUME_DIR`),不会丢数据。

---

## RAGAS 评测

系统内置基于 [RAGAS](https://docs.ragas.io/) 的评测链路,对真实检索 + 生成链路打分:

```bash
uv run python evaluation/ragas_eval.py            # 自动准备评测库并跑 5 项指标
uv run python evaluation/ragas_eval.py --limit 5  # 只评测前 5 条
```

- 评测集:`data/ragas_eval.json`(问题 + 标准答案)
- 输出:控制台汇总 + `docs/ragas_eval_result.json`(每题明细)
- 指标:Faithfulness / Answer Relevancy / Context Precision / Context Recall / Answer Correctness

详见 [`docs/RAGAS评测指南.md`](docs/RAGAS评测指南.md) 与 [`docs/RAGAS评测报告.md`](docs/RAGAS评测报告.md)。

---

## 优化记录

系统已完成 17 项优化,详见 [`docs/optimization_summary.md`](docs/optimization_summary.md)。

### 已完成优化

| 类别 | 优化项 | 说明 |
|------|--------|------|
| 架构 | Alembic 数据库迁移 | 版本化迁移,支持增量更新 |
| 架构 | 深度健康检查 | `/health/deep` 检查各组件状态 |
| 架构 | 全局异常处理 | 统一错误响应,记录详细日志 |
| 架构 | 数据库连接池调优 | pool_size=20, max_overflow=10 |
| 安全 | 用户账号禁用 | `is_active` 字段,登录时检查 |
| 安全 | 接口限频 | 登录 5次/分钟,注册 3次/分钟 |
| 安全 | 操作审计日志 | 记录关键操作 |
| 安全 | 密码管理 | 用户改密 + 管理员重置 |
| 功能 | 用户头像 & 个人资料 | 昵称、邮箱、头像 |
| 功能 | 系统配置管理 | 界面化修改 LLM/检索参数 |
| 功能 | 对话重新生成 | 重新生成回答、删除消息 |
| 功能 | 管理后台仪表盘 | 数据概览、统计图表 |
| 性能 | Redis 缓存 | 验证码存储,重启不丢失 |
| 性能 | BM25 索引缓存 | LRU 缓存,避免重复建索引 |
| 前端 | 对话页面优化 | Markdown 渲染、代码高亮 |
| 运维 | 日志持久化 | 挂载日志目录,日志轮转 |
| 运维 | 数据库自动备份 | 定时备份脚本,保留7天 |

### 待优化

| 优化项 | 说明 |
|--------|------|
| 切块预览模块 | 集成 Docling/MinerU,提升 PDF 解析质量 |
| CORS 白名单 | 生产环境限制跨域来源 |
| 深色模式 | 前端主题切换 |
| 移动端适配 | 响应式布局 |

---

## 文档索引

| 文档 | 说明 |
|------|------|
| [`docs/使用说明.md`](docs/使用说明.md) | 连接信息、账号密码、部署排查 |
| [`docs/API.md`](docs/API.md) | 接口文档 |
| [`docs/optimization_summary.md`](docs/optimization_summary.md) | 优化总结(17项) |
| [`docs/chunk_preview_optimization.md`](docs/chunk_preview_optimization.md) | 切块预览优化方案 |
| [`docs/RAGAS评测指南.md`](docs/RAGAS评测指南.md) | RAGAS 评测使用指南 |
| [`docs/RAGAS评测报告.md`](docs/RAGAS评测报告.md) | RAGAS 评测结果 |
| [`docs/admin_system_design.md`](docs/admin_system_design.md) | 管理后台设计文档 |

---

## 许可证

内部项目,仅限企业内部使用。
