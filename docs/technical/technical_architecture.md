# 企业内容知识问答系统 - 技术架构文档

## 一、项目概述

### 1.1 项目简介

本系统是一个基于 **RAG（检索增强生成）** 技术的企业级知识问答平台。用户可以上传企业文档到知识库，系统自动进行文档解析、文本切分、向量化存储，当用户提问时，系统检索相关上下文，由大语言模型生成准确回答并标注来源。

### 1.2 核心价值

- **知识沉淀**：将企业散落的文档资料统一管理
- **智能问答**：基于大模型的自然语言交互
- **来源可溯**：回答标注引用来源，可追溯验证
- **权限隔离**：按部门隔离知识库，支持多级权限管理

### 1.3 应用场景

- 企业内部知识库问答
- 员工手册/规章制度查询
- 产品文档/FAQ 智能客服
- 技术文档检索

---

## 二、系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                           用户浏览器                                  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTP/HTTPS
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Nginx (前端 + 反向代理)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────────┐│
│  │   Vue3 SPA   │  │  静态资源     │  │  /api → backend:8000        ││
│  └──────────────┘  └──────────────┘  └─────────────────────────────┘│
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI 后端服务                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │   API 层    │  │  Service 层  │  │   RAG 引擎   │  │  安全模块   ││
│  │  (路由)     │  │  (业务逻辑)  │  │ (检索/生成)  │  │ (JWT/验证码) ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘│
└────────┬───────────────┬───────────────┬───────────────┬───────────┘
         │               │               │               │
         ▼               ▼               ▼               ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │  MySQL  │    │  Redis  │    │ Milvus  │    │  DashScope  │
    │ (关系库) │    │ (缓存)  │    │ (向量库) │    │  (大模型API) │
    └─────────┘    └─────────┘    └─────────┘    └─────────────┘
```

### 2.2 技术栈总览

| 层级 | 技术选型 | 版本 | 说明 |
|------|----------|------|------|
| **前端** | Vue 3 + TypeScript | 3.x | 响应式 UI 框架 |
| | Element Plus | 2.x | UI 组件库 |
| | Vite | 5.x | 构建工具 |
| | Pinia | 2.x | 状态管理 |
| | Vue Router | 4.x | 路由管理 |
| | Axios | 1.x | HTTP 客户端 |
| **后端** | FastAPI | 0.110+ | 高性能异步 Web 框架 |
| | SQLAlchemy | 2.x | ORM 框架 |
| | Pydantic | 2.x | 数据验证 |
| | PyJWT | 2.x | JWT 认证 |
| | Alembic | 1.x | 数据库迁移 |
| | slowapi | 0.1+ | 接口限频 |
| **数据库** | MySQL | 8.0 | 关系型数据库 |
| | Milvus | 2.4 | 向量数据库 |
| | Redis | 7.x | 缓存/会话存储 |
| **大模型** | 通义千问 qwen-max | - | 文本生成 |
| | text-embedding-v3 | - | 文本向量化 |
| **基础设施** | Docker | 24.x | 容器化部署 |
| | Docker Compose | 2.x | 服务编排 |
| | Nginx | 1.24 | 反向代理/静态资源 |

---

## 三、核心模块设计

### 3.1 RAG 检索增强生成

#### 3.1.1 处理流程

```
文档上传 → 文档解析 → 文本清洗 → 文本切分 → 向量化 → 存入 Milvus
                                                      ↓
用户提问 → 问题向量化 → 向量检索 → 相关文档块 → 构建 Prompt → LLM 生成 → 流式输出
                         ↓
                      BM25 检索
                         ↓
                      混合排序
```

#### 3.1.2 文档解析

| 文件类型 | 解析方式 | 说明 |
|----------|----------|------|
| PDF | pypdf | 逐页提取文本 |
| PPT/PPTX | python-pptx | 提取幻灯片文本 |
| TXT/MD | 直接读取 | UTF-8 编码 |
| 图片 | 暂不解析 | 预留 OCR 接口 |

#### 3.1.3 文本切分策略

采用 **父子分块** 策略：

```
原始文档
    │
    ▼
┌─────────────────────────────────────┐
│         父块 (Parent Chunk)          │
│  chunk_size: 2000 字符               │
│  作用: 提供完整上下文                  │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  子块 1     │ │  子块 2     │ │  子块 3     │
│ 500 字符    │ │ 500 字符    │ │ 500 字符    │
│ 用于检索    │ │ 用于检索    │ │ 用于检索    │
└─────────────┘ └─────────────┘ └─────────────┘
```

**切分算法**：`RecursiveCharacterTextSplitter`
- 分隔符优先级：`\n\n` → `\n` → `。` → `!` → `?` → `;` → ` ` → ``
- 支持配置：chunk_size、chunk_overlap、parent_chunk_size

#### 3.1.4 检索策略

| 检索类型 | 说明 | 适用场景 |
|----------|------|----------|
| Dense | 纯向量检索 | 语义相似度匹配 |
| Hybrid | 向量 + BM25 混合 | 综合效果最佳（默认） |

**混合检索流程**：
1. 向量检索：Top 20 结果
2. BM25 检索：Top 20 结果
3. RRF 融合排序：取 Top 5
4. 送入 LLM 生成回答

#### 3.1.5 Prompt 工程

```
你是一个专业的知识问答助手。请根据以下参考资料回答用户问题。

参考资料：
{context}

用户问题：{question}

要求：
1. 只基于参考资料回答，不要编造信息
2. 如果参考资料中没有相关内容，请明确说明
3. 在回答中使用 [1][2] 等编号标注引用来源
4. 回答要准确、简洁、专业
```

### 3.2 用户认证与权限

#### 3.2.1 认证流程

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  获取     │    │  输入     │    │  登录     │    │  获取     │
│  验证码   │───▶│  用户信息 │───▶│  验证     │───▶│  Token   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                     │
                                                     ▼
                                              ┌──────────┐
                                              │  后续请求  │
                                              │  携带Token│
                                              └──────────┘
```

#### 3.2.2 JWT Token 设计

```json
{
  "sub": "user_id",
  "username": "zhangsan",
  "role": "employee",
  "department_id": 1,
  "exp": 1735689600
}
```

- 过期时间：24 小时
- 签名算法：HS256
- 存储位置：localStorage

#### 3.2.3 RBAC 权限模型

```
┌─────────────────────────────────────────────────────────┐
│                      权限层级                            │
├─────────────────────────────────────────────────────────┤
│  super_admin（超级管理员）                                │
│  ├── 所有部门知识库管理                                   │
│  ├── 用户管理（CRUD + 角色分配）                          │
│  ├── 部门管理                                            │
│  ├── 系统配置                                            │
│  ├── 审计日志查看                                         │
│  └── 仪表盘统计                                          │
├─────────────────────────────────────────────────────────┤
│  dept_admin（部门管理员）                                 │
│  ├── 本部门知识库管理                                     │
│  ├── 本部门文档管理                                       │
│  └── 问答功能                                            │
├─────────────────────────────────────────────────────────┤
│  employee（普通员工）                                     │
│  ├── 本部门知识库查看                                     │
│  ├── 公开知识库使用                                       │
│  └── 问答功能                                            │
└─────────────────────────────────────────────────────────┘
```

### 3.3 管理后台

#### 3.3.1 功能模块

| 模块 | 功能 | 权限 |
|------|------|------|
| 用户管理 | 用户列表、编辑、删除、角色分配、部门分配、禁用/启用、重置密码 | super_admin |
| 部门管理 | 部门列表、创建、编辑、删除 | super_admin |
| 权限管理 | 角色列表、权限矩阵可视化 | super_admin |
| 系统配置 | LLM 参数、检索参数、验证码开关 | super_admin |
| 审计日志 | 操作记录查看、筛选 | super_admin |
| 仪表盘 | 用户/知识库/文档/对话统计 | admin |

#### 3.3.2 审计日志设计

记录关键操作：

| 操作类型 | 说明 |
|----------|------|
| create_user | 创建用户 |
| delete_user | 删除用户 |
| update_role | 修改角色 |
| update_department | 修改部门 |
| toggle_user_status | 禁用/启用用户 |
| reset_password | 重置密码 |
| create_kb | 创建知识库 |
| delete_kb | 删除知识库 |

---

## 四、数据库设计

### 4.1 ER 图

```
┌─────────────┐       ┌─────────────┐
│  departments │       │    users    │
├─────────────┤       ├─────────────┤
│ id (PK)     │◀──┐   │ id (PK)     │
│ name        │   └───│ department_id│ (FK)
│ created_at  │       │ username    │
└─────────────┘       │ password    │
                      │ role        │
                      │ is_active   │
                      │ nickname    │
                      │ email       │
                      │ avatar_url  │
                      │ created_at  │
                      └──────┬──────┘
                             │
                             ▼
┌─────────────────┐    ┌─────────────┐
│ knowledge_bases │    │  documents  │
├─────────────────┤    ├─────────────┤
│ id (PK)         │◀───│ id (PK)     │
│ name            │    │ kb_id       │ (FK)
│ department_id   │    │ filename    │
│ is_public       │    │ file_path   │
│ retrieval_type  │    │ status      │
│ chunk_size      │    │ chunk_count │
│ chunk_overlap   │    │ version     │
│ parent_chunk_size│   │ created_at  │
│ doc_count       │    └──────┬──────┘
│ created_at      │           │
└─────────────────┘           ▼
                      ┌─────────────┐
                      │   chunks    │
                      ├─────────────┤
                      │ id (PK)     │
                      │ kb_id       │ (FK)
                      │ document_id │ (FK)
                      │ content     │
                      │ chunk_index │
                      │ parent_id   │ (FK, 自引用)
                      │ milvus_id   │
                      │ content_hash│
                      │ version     │
                      │ created_at  │
                      └─────────────┘

┌──────────────┐    ┌──────────────┐
│ chat_sessions │    │ chat_messages │
├──────────────┤    ├──────────────┤
│ id (PK)      │◀───│ id (PK)      │
│ user_id      │    │ session_id   │ (FK)
│ name         │    │ role         │
│ created_at   │    │ content      │
│ updated_at   │    │ citations    │ (JSON)
└──────────────┘    │ kb_ids       │ (JSON)
                    │ created_at   │
                    └──────────────┘

┌──────────────┐    ┌──────────────┐
│  audit_logs  │    │system_configs│
├──────────────┤    ├──────────────┤
│ id (PK)      │    │ id (PK)      │
│ user_id      │    │ key          │
│ username     │    │ value        │
│ action       │    │ description  │
│ target_type  │    │ updated_at   │
│ target_id    │    └──────────────┘
│ target_name  │
│ detail       │
│ ip_address   │
│ created_at   │
└──────────────┘
```

### 4.2 表结构详解

#### users 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK | 用户ID |
| username | VARCHAR(64), UNIQUE | 用户名 |
| password | VARCHAR(128) | 密码(bcrypt 哈希) |
| role | VARCHAR(32) | 角色(super_admin/dept_admin/employee) |
| department_id | INT, FK | 所属部门 |
| is_active | BOOLEAN | 是否启用 |
| nickname | VARCHAR(64) | 昵称 |
| email | VARCHAR(128) | 邮箱 |
| avatar_url | VARCHAR(256) | 头像URL |
| created_at | DATETIME | 创建时间 |

#### chunks 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK | 块ID |
| kb_id | INT, FK | 知识库ID |
| document_id | INT, FK | 文档ID |
| content | TEXT | 文本内容 |
| chunk_index | INT | 块序号 |
| parent_id | INT, FK | 父块ID(自引用) |
| milvus_id | VARCHAR(64) | Milvus 中的向量ID |
| content_hash | VARCHAR(64) | 内容 SHA-256(增量更新用) |
| version | INT | 版本号 |
| created_at | DATETIME | 创建时间 |

---

## 五、API 设计

### 5.1 RESTful 规范

- 统一前缀：`/api`
- 认证方式：Bearer Token (JWT)
- 响应格式：JSON
- 错误码：HTTP 标准状态码

### 5.2 接口分组

| 模块 | 前缀 | 接口数 | 说明 |
|------|------|--------|------|
| 认证 | /api/auth | 7 | 登录/注册/验证码/密码/个人信息 |
| 知识库 | /api/knowledge-bases | 5 | CRUD + 文档管理 |
| 文档块 | /api/chunks | 3 | 查看/编辑/删除 |
| 对话 | /api/chat | 7 | 会话管理 + 流式问答 |
| 管理后台 | /api/admin | 18 | 用户/部门/权限/配置/日志/仪表盘 |
| 系统 | /health | 2 | 健康检查 |

### 5.3 流式响应设计

采用 **Server-Sent Events (SSE)** 实现流式输出：

```
Content-Type: text/event-stream

data: {"token": "工作"}
data: {"token": "满1年"}
data: {"token": "不满3年"}
...
data: {"citations": [{"index": 1, "kb_id": 6, "chunk_id": 42}]}
data: [DONE]
```

**优势**：
- 实时输出，用户体验好
- 单向推送，实现简单
- 自动重连

---

## 六、安全设计

### 6.1 认证安全

| 措施 | 说明 |
|------|------|
| 密码加密 | bcrypt 哈希，加盐存储 |
| JWT 签名 | HS256 算法，服务端密钥 |
| Token 过期 | 24 小时自动失效 |
| 验证码 | 图形验证码防机器人，Redis 存储(5分钟过期) |

### 6.2 接口安全

| 措施 | 说明 |
|------|------|
| 接口限频 | 登录 5次/分钟，注册 3次/分钟 |
| 权限校验 | RBAC 角色 + 部门隔离 |
| 参数验证 | Pydantic 严格校验 |
| SQL 注入防护 | SQLAlchemy ORM 参数化查询 |

### 6.3 数据安全

| 措施 | 说明 |
|------|------|
| 部门隔离 | 知识库按部门隔离，跨部门不可见 |
| 公开库控制 | 仅 super_admin 可创建公开库 |
| 文件校验 | 上传文件类型、大小限制 |
| 审计日志 | 关键操作记录可追溯 |

---

## 七、性能优化

### 7.1 缓存策略

| 缓存对象 | 存储 | 过期时间 | 说明 |
|----------|------|----------|------|
| 验证码 | Redis | 5 分钟 | 防重复提交 |
| BM25 索引 | 内存 LRU | 最多 50 个 | 避免重复构建 |
| 会话数据 | Redis | 24 小时 | 减少数据库查询 |

### 7.2 数据库优化

| 优化项 | 配置 | 说明 |
|--------|------|------|
| 连接池 | pool_size=20 | 连接复用 |
| 最大溢出 | max_overflow=10 | 峰值扩展 |
| 连接超时 | pool_timeout=30s | 防阻塞 |
| 索引优化 | 字段索引 | 查询加速 |

### 7.3 向量检索优化

| 优化项 | 说明 |
|--------|------|
| 索引类型 | IVF_FLAT（默认） |
| 混合检索 | 向量 + BM25 RRF 融合 |
| 批量写入 | 减少 Milvus 交互次数 |
| 增量更新 | 按内容哈希复用未变化向量 |

---

## 八、部署架构

### 8.1 Docker 服务编排

```yaml
services:
  frontend:    # Vue3 + Nginx
    ports: 8080:80
    
  backend:     # FastAPI
    ports: 8000:8000
    depends_on: [mysql, milvus, redis]
    
  mysql:       # 关系数据库
    ports: 3306:3306
    
  redis:       # 缓存
    ports: 6379:6379
    
  milvus:      # 向量数据库
    ports: 19530:19530
    
  etcd:        # Milvus 元数据
    internal
    
  minio:       # Milvus 对象存储
    internal
```

### 8.2 网络架构

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                       │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │ frontend │───▶│ backend  │───▶│  mysql   │          │
│  │  :8080   │    │  :8000   │    │  :3306   │          │
│  └──────────┘    └────┬─────┘    └──────────┘          │
│                       │                                 │
│                       ├────────▶┌──────────┐           │
│                       │         │  redis   │           │
│                       │         │  :6379   │           │
│                       │         └──────────┘           │
│                       │                                 │
│                       └────────▶┌──────────┐           │
│                                 │  milvus  │           │
│                                 │ :19530   │           │
│                                 └──────────┘           │
└─────────────────────────────────────────────────────────┘
```

### 8.3 数据持久化

| 服务 | 卷挂载 | 说明 |
|------|--------|------|
| MySQL | mysql_data:/var/lib/mysql | 数据库文件 |
| Redis | redis_data:/data | 持久化数据 |
| Milvus | milvus_data:/var/lib/milvus | 向量数据 |
| Backend | ./data:/app/data | 上传文件/日志 |
| Backend | ./logs:/app/logs | 日志文件 |
| Backend | ./alembic:/app/alembic | 迁移脚本 |

---

## 九、开发规范

### 9.1 代码结构

```
app/
├── api/              # 路由层：接口定义、参数校验
├── services/         # 业务层：核心业务逻辑
├── models/           # 数据层：ORM 模型
├── schemas/          # 协议层：Pydantic 数据模型
├── rag/              # RAG 引擎：解析/向量/检索/生成
└── main.py           # 入口：中间件、异常处理、路由注册
```

### 9.2 分层职责

| 层级 | 职责 | 示例 |
|------|------|------|
| API 层 | 路由定义、参数校验、权限校验 | `@router.post("/login")` |
| Service 层 | 业务逻辑、事务管理 | `auth_service.login()` |
| Model 层 | 数据库操作、ORM 映射 | `User.query.filter()` |
| Schema 层 | 数据序列化、验证 | `UserOut.model_validate()` |

### 9.3 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件名 | 小写下划线 | `auth_service.py` |
| 类名 | 大驼峰 | `ChatMessage` |
| 函数名 | 小写下划线 | `get_current_user()` |
| 常量 | 大写下划线 | `MAX_UPLOAD_SIZE` |
| API 路径 | kebab-case | `/api/chat-sessions` |

### 9.4 错误处理

```python
# 统一异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"未捕获异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"}
    )

# 业务异常
class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
```

---

## 十、测试策略

### 10.1 测试类型

| 类型 | 工具 | 覆盖范围 |
|------|------|----------|
| 单元测试 | pytest | Service 层业务逻辑 |
| 集成测试 | pytest + httpx | API 接口测试 |
| 评测 | RAGAS | RAG 质量评估 |

### 10.2 RAGAS 评测指标

| 指标 | 说明 |
|------|------|
| Faithfulness | 回答是否基于检索内容 |
| Answer Relevancy | 回答与问题的相关性 |
| Context Precision | 检索结果的精确度 |
| Context Recall | 检索结果的召回率 |
| Answer Correctness | 回答的正确性 |

---

## 十一、监控与运维

### 11.1 日志规范

```
时间 | 级别 | 模块 | 消息
2024-01-01 12:00:00 | INFO | auth_service | 用户登录成功: zhangsan
```

**日志级别**：
- DEBUG：调试信息
- INFO：正常操作
- WARNING：警告信息
- ERROR：错误信息
- CRITICAL：严重错误

### 11.2 健康检查

| 接口 | 说明 |
|------|------|
| GET /health | 基础存活探测 |
| GET /health/deep | 深度检查(MySQL/Milvus/Redis) |

### 11.3 监控指标

| 指标 | 说明 |
|------|------|
| 请求耗时 | 接口响应时间 |
| 错误率 | 4xx/5xx 请求比例 |
| 活跃用户 | 在线用户数 |
| 知识库规模 | 文档数/块数 |

---

## 十二、扩展性设计

### 12.1 水平扩展

```
┌─────────────┐
│   Nginx     │ (负载均衡)
└──────┬──────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│ Backend1 │   │ Backend2 │   │ Backend3 │
└──────────┘   └──────────┘   └──────────┘
       │              │              │
       └──────────────┴──────────────┘
                      │
                      ▼
              ┌──────────────┐
              │ MySQL/Milvus │ (共享存储)
              └──────────────┘
```

### 12.2 功能扩展点

| 扩展点 | 说明 |
|--------|------|
| 解析器 | 新增文件类型支持（MinerU/Docling） |
| 向量库 | 支持切换到 Qdrant/Weaviate |
| 大模型 | 支持 OpenAI/Claude/本地模型 |
| 存储 | 支持 OSS/S3 对象存储 |
| 认证 | 支持 LDAP/SSO 集成 |

---

## 附录 A：技术文档索引

| 文档 | 说明 |
|------|------|
| README.md | 项目简介、快速开始 |
| docs/使用说明.md | 部署配置、账号密码、常见问题 |
| docs/API.md | 接口文档 |
| docs/optimization_summary.md | 优化记录(17项) |
| docs/chunk_preview_optimization.md | 切块预览优化方案 |
| docs/RAGAS评测指南.md | RAGAS 评测使用指南 |

## 附录 B：依赖清单

### 后端依赖 (pyproject.toml)

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.25
pymysql>=1.1.0
pyjwt>=2.8.0
bcrypt>=4.1.2
pillow>=10.2.0
langchain>=0.1.0
langchain-core>=0.1.10
langchain-community>=0.0.10
langchain-text-splitters>=0.0.1
pymilvus>=2.4.0
dashscope>=1.14.0
redis>=5.0.0
alembic>=1.13.0
slowapi>=0.1.9
```

### 前端依赖 (package.json)

```json
{
  "vue": "^3.4.0",
  "vue-router": "^4.3.0",
  "pinia": "^2.1.0",
  "element-plus": "^2.5.0",
  "axios": "^1.6.0",
  "vite": "^5.1.0",
  "typescript": "^5.3.0"
}
```

---

**文档版本**：v1.0.0  
**最后更新**：2024年1月  
**维护者**：开发团队
