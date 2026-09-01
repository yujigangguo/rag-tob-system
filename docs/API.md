# RAG System 接口文档

基于 FastAPI 的 RAG(检索增强生成)问答服务接口说明。**除 `/health` 外所有接口均需登录后携带 `Authorization: Bearer <token>`**;统一前缀 `/api`。

## 1. 服务信息

| 项 | 值 |
|----|-----|
| 服务框架 | FastAPI |
| 默认地址 | `http://127.0.0.1:8000`(Docker 内 `http://backend:8000`) |
| 交互式文档 | Swagger UI `http://127.0.0.1:8000/docs`、ReDoc `/redoc` |
| 启动命令 | `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000` |

> 权限说明:系统采用三级角色(`super_admin` / `dept_admin` / `employee`)+ 部门隔离,详见 `docs/使用说明.md`。接口标注「仅管理员」的仅 `super_admin` / `dept_admin`(本部门)可调用。标注「仅超管」的仅 `super_admin` 可调用。

---

## 2. 认证

### 2.1 获取图形验证码

**`GET /api/auth/captcha`**

```json
{ "captcha_id": "cap_...", "captcha_image": "data:image/png;base64,..." }
```

### 2.2 注册

**`POST /api/auth/register`** — 首个用户自动成为 `super_admin`，后续默认 `employee`

```json
{ "username": "zhangsan", "password": "abc123456", "confirm_password": "abc123456",
  "captcha_id": "cap_...", "captcha_code": "AB12" }
```

### 2.3 登录

**`POST /api/auth/login`**

请求同上(用户名/密码/验证码)。响应:

```json
{
  "access_token": "eyJ...", "token_type": "bearer",
  "username": "zhangsan", "role": "employee",
  "department_id": 1, "department_name": "研发部"
}
```

### 2.4 当前用户

**`GET /api/auth/me`**

```json
{
  "id": 2, "username": "zhangsan", "role": "employee",
  "department_id": 1, "department_name": "研发部",
  "nickname": "张三", "email": "zhangsan@example.com", "avatar_url": null
}
```

### 2.5 修改密码

**`POST /api/auth/change-password`**

```json
{ "old_password": "abc123456", "new_password": "new123456" }
```

### 2.6 更新个人信息

**`PUT /api/auth/profile`**

| 字段 | 类型 | 说明 |
|------|------|------|
| nickname | string | 昵称 |
| email | string | 邮箱 |
| avatar_url | string | 头像URL(base64或链接) |

---

## 3. 部门

**`GET /api/departments`** — 部门列表(登录即可)

```json
[ { "id": 1, "name": "研发部" }, { "id": 5, "name": "产品" } ]
```

---

## 4. 知识库

### 4.1 创建(仅管理员)

**`POST /api/knowledge-bases`**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 知识库名称 |
| department_id | int | 是 | 所属部门(dept_admin 只能选本部门) |
| is_public | bool | 否 | 全公司可见,默认 false(**仅 super_admin 可设 true**) |
| retrieval_type | string | 否 | `dense` / `hybrid`(默认 hybrid) |
| chunk_size / chunk_overlap / parent_chunk_size | int | 否 | 子块/重叠/父块大小(默认 500/50/2000) |

响应(KnowledgeBaseOut):

```json
{
  "id": 7, "name": "产品知识库", "description": null,
  "department_id": 5, "is_public": false,
  "retrieval_type": "hybrid", "chunk_size": 500, "chunk_overlap": 50,
  "parent_chunk_size": 2000, "doc_count": 0, "created_at": "2026-08-24T10:00:00"
}
```

### 4.2 列表 / 详情 / 更新 / 删除

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/knowledge-bases` | 登录 | 本部门库 + 公开库(公开排前) |
| GET | `/api/knowledge-bases/{id}` | 登录 | 详情(不可见返回 404) |
| PUT | `/api/knowledge-bases/{id}` | 仅管理员 | 更新;`department_id` / `is_public` 仅 super_admin 可改 |
| DELETE | `/api/knowledge-bases/{id}` | 仅管理员 | 删除(同步删 Milvus collection 与 MySQL 记录) |

---

## 5. 文档与文档块

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/api/knowledge-bases/{kb}/documents` | **仅管理员** | 上传文档(multipart,`file` 字段;`chunk_size`/`chunk_overlap` 可选覆盖);单文件 ≤ `MAX_UPLOAD_SIZE_MB`(默认 10),超限返回 413;后台异步解析,立即返回 |
| GET | `/api/knowledge-bases/{kb}/documents` | 登录 | 文档列表 |
| GET | `/api/knowledge-bases/{kb}/documents/{id}/progress` | 登录 | 解析进度 `{progress, status}`(pending/parsing/completed/failed) |
| GET | `/api/knowledge-bases/{kb}/documents/{id}/chunks` | 登录 | 文档块列表(仅父块) |
| DELETE | `/api/knowledge-bases/{kb}/documents/{id}` | **仅管理员** | 删除文档(向量 + 记录 + 文件) |
| PUT | `/api/chunks/{id}` | **仅管理员** | 编辑父块(重新切分 + 向量化),body `{"content": "..."}` |
| DELETE | `/api/chunks/{id}` | **仅管理员** | 删除文档块(连同子块与向量) |

---

## 6. 对话

### 6.1 会话管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/chat/sessions` | 会话列表 |
| POST | `/api/chat/sessions` | 新建会话,body `{"name": "新对话"}` |
| PUT | `/api/chat/sessions/{id}` | 重命名 |
| DELETE | `/api/chat/sessions/{id}` | 删除会话 |
| GET | `/api/chat/sessions/{id}/messages` | 消息列表 |

消息(ChatMessageOut):

```json
{
  "id": 12, "session_id": 3, "role": "assistant",
  "content": "工作满1年不满3年的员工,每年享有5天带薪年假。[1]",
  "citations": [ { "index": 1, "kb_id": 6, "document_id": 18, "chunk_id": 42 } ],
  "kb_ids": [6],
  "created_at": "2026-08-24T10:00:00"
}
```

- `citations`:回答中 [N] 的引用映射(前端据此渲染可点击跳转链接);
- `kb_ids`:本次问答检索的知识库 id 列表(历史追溯 / 评测用);旧消息为 null。

### 6.2 流式问答(SSE)

**`POST /api/chat/stream`**(所有登录用户可用,按部门可见性校验知识库)

请求:

```json
{
  "session_id": null, "question": "年假有几天?",
  "kb_ids": [6], "model": "qwen-max",
  "temperature": 0.7, "top_p": 0.8, "max_tokens": 2048, "history_rounds": 5
}
```

响应为 `text/event-stream`,事件序列:

```
data: {"token": "工作"}
data: {"token": "满1年"}
...
data: {"citations": [{"index": 1, "kb_id": 6, "document_id": 18, "chunk_id": 42}]}
data: [DONE]
```

- `token` 事件逐字累积为回答文本;
- `citations` 事件在 [DONE] 前下发一次(无引用时省略);
- 出错时下发 `data: {"error": "..."}`。

---

## 7. 系统接口

### 7.1 基础健康检查

**`GET /health`**

```json
{ "status": "ok" }
```

### 7.2 深度健康检查

**`GET /health/deep`**

```json
{
  "status": "ok",
  "components": {
    "mysql": { "status": "ok", "latency_ms": 2 },
    "milvus": { "status": "ok", "latency_ms": 5 },
    "redis": { "status": "ok", "latency_ms": 1 }
  }
}
```

### 7.3 接口限频说明

| 接口 | 限频 | 说明 |
|------|------|------|
| POST /api/auth/login | 5次/分钟/IP | 防暴力破解 |
| POST /api/auth/register | 3次/分钟/IP | 防刷注册 |
| 其他接口 | 60次/分钟/IP | 通用限制 |

超过限制返回 `429 Too Many Requests`。

---

## 8. 管理后台接口(需超级管理员)

### 8.1 用户管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/users` | 用户列表(分页/搜索/筛选) |
| GET | `/api/admin/users/{id}` | 用户详情 |
| PUT | `/api/admin/users/{id}` | 更新用户 |
| DELETE | `/api/admin/users/{id}` | 删除用户 |
| PUT | `/api/admin/users/{id}/role` | 分配角色 |
| PUT | `/api/admin/users/{id}/department` | 分配部门 |
| PUT | `/api/admin/users/{id}/status` | 禁用/启用用户 |
| POST | `/api/admin/users/{id}/reset-password` | 重置密码 |

**用户列表查询参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码(默认1) |
| page_size | int | 每页数量(默认20) |
| keyword | string | 搜索关键词(用户名/昵称) |
| role | string | 角色筛选 |
| is_active | bool | 状态筛选 |

**分配角色请求:**

```json
{ "role": "dept_admin" }
```

**重置密码请求:**

```json
{ "new_password": "new123456" }
```

### 8.2 部门管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/departments` | 部门列表(含用户数) |
| POST | `/api/admin/departments` | 创建部门 |
| PUT | `/api/admin/departments/{id}` | 更新部门 |
| DELETE | `/api/admin/departments/{id}` | 删除部门 |

### 8.3 权限管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/roles` | 角色列表 |
| GET | `/api/admin/permissions` | 权限配置 |

**角色列表响应:**

```json
[
  { "key": "super_admin", "name": "超级管理员", "description": "系统管理员，所有部门" },
  { "key": "dept_admin", "name": "部门管理员", "description": "本部门管理员" },
  { "key": "employee", "name": "普通员工", "description": "只读+问答" }
]
```

### 8.4 系统配置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/configs` | 获取所有配置 |
| PUT | `/api/admin/configs/{key}` | 更新配置 |

**配置列表响应:**

```json
[
  { "id": 1, "key": "llm_model", "value": "qwen-max", "description": "LLM 模型名称" },
  { "id": 2, "key": "llm_temperature", "value": "0.7", "description": "LLM 温度参数" },
  { "id": 3, "key": "retrieval_top_k", "value": "20", "description": "检索召回数量" }
]
```

### 8.5 审计日志

**`GET /api/admin/audit-logs`**

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| page_size | int | 每页数量 |
| action | string | 操作类型筛选 |
| username | string | 操作人筛选 |

**响应:**

```json
{
  "items": [
    {
      "id": 1,
      "username": "admin",
      "action": "update_role",
      "target_type": "user",
      "target_id": 5,
      "target_name": "zhangsan",
      "detail": "角色改为 dept_admin",
      "ip_address": "127.0.0.1",
      "created_at": "2024-01-01T12:00:00"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 50
}
```

### 8.6 仪表盘统计

**`GET /api/admin/dashboard`**

```json
{
  "users": {
    "total": 100,
    "active": 95,
    "new_this_week": 10
  },
  "knowledge_bases": {
    "total": 20
  },
  "documents": {
    "total": 500
  },
  "conversations": {
    "sessions": 1000,
    "messages": 5000
  }
}
```

---

## 9. 对话高级接口

### 9.1 重新生成

**`POST /api/chat/regenerate`**

删除最后一条助手消息并返回用户问题，前端可重新发送。

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | int | 会话ID |

**响应:**

```json
{
  "session_id": 3,
  "question": "年假有几天?",
  "message": "已删除最后一条回复，请重新提问"
}
```

### 9.2 删除消息

**`DELETE /api/chat/messages/{message_id}`**

删除指定消息及其后续消息。

---

## 10. 调用示例

```bash
# 1. 登录拿 token
curl.exe -X POST http://127.0.0.1:8000/api/auth/login -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"***\",\"captcha_id\":\"cap_...\",\"captcha_code\":\"AB12\"}"

# 2. 带 token 创建知识库(仅管理员)
curl.exe -X POST http://127.0.0.1:8000/api/knowledge-bases -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"产品知识库\",\"department_id\":5,\"is_public\":false}"

# 3. 流式问答
curl.exe -N -X POST http://127.0.0.1:8000/api/chat/stream -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" -d "{\"question\":\"年假有几天?\",\"kb_ids\":[6]}"

# 4. 获取管理后台仪表盘
curl.exe http://127.0.0.1:8000/api/admin/dashboard -H "Authorization: Bearer <token>"

# 5. 获取审计日志
curl.exe "http://127.0.0.1:8000/api/admin/audit-logs?page=1&page_size=10" -H "Authorization: Bearer <token>"

# 6. 深度健康检查
curl.exe http://127.0.0.1:8000/health/deep
```

> 编码注意:Windows PowerShell 5.1 的 `Invoke-RestMethod` 对中文有 GBK 编码坑,建议用 `curl.exe`、Python `httpx` 或浏览器 `/docs`。
