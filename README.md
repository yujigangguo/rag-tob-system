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
| 测试 | pytest |

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
├── data/                   # 上传文件、测试文档
├── docker-compose.yml      # MySQL(8.0)
├── .env.example            # 配置模板
└── pyproject.toml          # 后端依赖(uv)
```

## 功能特性

- **用户认证**:注册 / 登录,图形验证码 + JWT,密码 bcrypt 哈希
- **多知识库**:按用户隔离,支持稠密/混合检索,自定义切块参数
- **文档解析**:PDF / PPT / Markdown / TXT / 图片(图片暂不 OCR),后台异步解析 + 真实进度条,切分向量化入 Milvus
- **文档块管理**:预览、编辑(自动重向量化)、删除
- **智能问答**:多知识库联合检索、流式输出、历史多轮对话、参数可调(温度/TopP/最大token/历史轮数)
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
uv run pytest                 # 12 项测试(问答测试需配置 LLM_API_KEY)
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

## 主要接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/auth/captcha` | 获取图形验证码 |
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| POST | `/api/knowledge-bases` | 创建知识库 |
| GET | `/api/knowledge-bases` | 知识库列表 |
| POST | `/api/knowledge-bases/{id}/documents` | 上传文档(后台异步解析) |
| GET | `/api/knowledge-bases/{id}/documents/{doc_id}/progress` | 查询文档解析进度 |
| GET/PUT/DELETE | `/api/chunks/{id}` | 文档块编辑/删除 |
| POST | `/api/chat/stream` | 流式问答(SSE) |
| GET/POST/DELETE | `/api/chat/sessions` | 会话管理 |

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

## 检索命中率评估

对评测集跑检索,统计 Recall@k 命中率(判断召回文本是否命中答案关键词):

```bash
# 1. 准备评测集(可参考 data/eval.json)
# 2. 确保知识库已上传文档并解析完成
uv run python scripts/eval.py --kb-id 1 --dataset data/eval.json --top-k 5
```

评测集 JSON 格式:

```json
[{ "question": "年假有几天?", "keywords": ["5 天", "10 天", "15 天"] }]
```

输出每个问题的命中情况与整体 `Recall@k`,用于评估检索质量、发现知识库覆盖不足。
