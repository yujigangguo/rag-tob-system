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
| 大模型 | 通义千问 qwen-max(流式)+ text-embedding(向量化) |
| 测试/评测 | pytest(17 项)+ RAGAS 0.2(evaluation/) |

## 目录结构

```
rag-system/
├── backend 相关(项目根)
│   ├── app/                # FastAPI 应用
│   │   ├── main.py         # 入口
│   │   ├── database.py     # SQLAlchemy
│   │   ├── security.py     # JWT / 密码 / 验证码
│   │   ├── models/         # ORM 模型
│   │   ├── schemas/        # Pydantic
│   │   ├── api/            # 路由
│   │   ├── services/       # 业务逻辑
│   │   └── rag/            # RAG 引擎(解析/向量/检索/生成)
│   ├── config/settings.py  # 配置
│   └── tests/              # pytest 测试
├── frontend/               # Vue3 前端
│   └── src/views/          # 登录/注册/对话/知识库管理/详情
├── data/                   # 上传文件、测试文档、演示数据、评测集
├── evaluation/             # RAGAS 评测(管线 + 入口)
├── scripts/                # init_rbac 迁移 / generate_demo_data / selfcheck 等
├── docs/                   # 使用说明 / API / 演示文档 / RAGAS 报告 / Bug 修复历程
├── docker-compose.yml      # Milvus + MySQL + 后端 + 前端
├── .env.example            # 配置模板
└── pyproject.toml          # 后端依赖(uv)
```

## 功能特性

- **用户认证**:注册 / 登录,图形验证码 + JWT,密码 bcrypt 哈希
- **三级角色权限**:`super_admin`(系统管理员,所有部门)/ `dept_admin`(部门管理员,本部门)/ `employee`(员工,只读 + 问答);知识库按**部门隔离**,支持**全公司可见的公开知识库**(仅超管可建可管)
- **多知识库**:按部门共享,支持稠密/混合检索,自定义切块参数(含父块大小)
- **文档解析**:PDF / PPT / Markdown / TXT / 图片(图片暂不 OCR),后台异步解析 + 真实进度条,**父子分块**(子块检索、父块作上下文)向量化入 Milvus;上传大小上限 10MB(可配)
- **文档块管理**:预览、编辑(自动重向量化)、删除(仅管理员)
- **智能问答**:多知识库联合检索、流式输出、历史多轮对话、参数可调(温度/TopP/最大token/历史轮数)
- **引用溯源**:回答标注 [1][2] 来源编号,**可点击跳转到知识库对应文档块并高亮**;历史消息记录"本次检索的知识库来源"与引用映射,便于追溯与评测
- **RAGAS 评测**:内置 `evaluation/ragas_eval.py`,一键跑 Faithfulness / Relevancy / Context Precision / Context Recall / Correctness 五指标
- **可观测性**:统一日志模块(控制台 + 文件)+ 请求日志中间件(方法/路径/状态码/耗时)

## 快速开始

### 方式 A:Docker 一键部署(推荐)

```bash
docker compose up -d --build   # 一键起 Milvus + MySQL + 后端 + 前端
```

- 前端:`http://localhost:8080`
- 后端文档:`http://localhost:8000/docs`

### 方式 B:本地开发(前后端分离)

```bash
# 1. 起基础设施(MySQL + Milvus)
docker compose up -d mysql milvus

# 2. 后端(uv)
uv sync
copy .env.example .env          # 填 LLM_API_KEY 与 EMBEDDING_API_KEY
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

## 关键配置(.env)

| 配置 | 说明 |
|------|------|
| `LLM_API_KEY` | 通义 DashScope API Key(qwen-max) |
| `EMBEDDING_API_KEY` | 通义 embedding API Key(可与上面相同) |
| `DB_*` | MySQL 连接(docker-compose 默认 `rag_user` / `rag_db`) |
| `MILVUS_URI` | Milvus 地址,默认 `http://localhost:19530` |
| `SECRET_KEY` | JWT 签名密钥,生产务必修改 |
| `DEFAULT_HISTORY_ROUNDS` | 默认历史对话轮数(5) |
| `MAX_UPLOAD_SIZE_MB` | 单文件上传上限,默认 10(需与前端 nginx `client_max_body_size` 一致) |

## 主要接口(均需 Bearer Token,前缀 `/api`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/auth/captcha` | 获取图形验证码 |
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录(返回角色/部门) |
| GET | `/api/auth/me` | 当前用户信息(角色/部门) |
| GET | `/api/departments` | 部门列表 |
| POST | `/api/knowledge-bases` | 创建知识库(仅管理员,含 `department_id` / `is_public`) |
| GET | `/api/knowledge-bases` | 知识库列表(部门可见 + 公开库) |
| PUT/DELETE | `/api/knowledge-bases/{id}` | 更新/删除(仅管理员) |
| POST | `/api/knowledge-bases/{id}/documents` | 上传文档(仅管理员,≤10MB,异步解析) |
| GET | `/api/knowledge-bases/{id}/documents/{doc_id}/progress` | 查询文档解析进度 |
| GET/PUT/DELETE | `/api/chunks/{id}` | 文档块查看/编辑/删除(编辑删除仅管理员) |
| POST | `/api/chat/stream` | 流式问答(SSE,含引用映射 citations) |
| GET/POST/PUT/DELETE | `/api/chat/sessions` | 会话管理 |
| GET | `/api/chat/sessions/{id}/messages` | 会话消息(含 citations / kb_ids) |

## Docker 一键部署

一键启动 MySQL + 后端 + 前端(nginx 托管并反向代理 `/api`,支持 SSE):

```bash
# 先在 .env 填好 LLM_API_KEY / EMBEDDING_API_KEY(Milvus 需在宿主机运行)
docker compose up -d --build
```

访问:

- 前端:`http://localhost:8080`
- 后端文档:`http://localhost:8000/docs`

```bash
docker compose down        # 停止
docker compose down -v     # 停止并清空 MySQL 数据
```

> 说明:Milvus 已纳入 compose,后端通过服务名 `milvus:19530` 访问;数据卷沿用本机 `E:/milvus_redis/volumes`(`.env` 的 `MILVUS_VOLUME_DIR`),不会丢数据。

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
