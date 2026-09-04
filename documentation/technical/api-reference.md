# API 接口文档

## 📋 概述

本文档描述 RAG 知识问答系统的后端 API 接口。

**基础信息：**
- 基础路径：`/api`
- 认证方式：Bearer Token (JWT)
- 内容类型：`application/json`

---

## 🔐 认证接口

### 获取验证码

```http
GET /api/auth/captcha
```

**响应：**
```json
{
  "captcha_id": "cap_1234567890_1234",
  "captcha_image": "data:image/png;base64,..."
}
```

### 用户登录

```http
POST /api/auth/login
```

**请求：**
```json
{
  "username": "admin",
  "password": "admin123",
  "captcha_id": "cap_1234567890_1234",
  "captcha_code": "ABCD"
}
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "username": "admin",
  "role": "super_admin",
  "department_id": 1,
  "department_name": "技术部"
}
```

### 用户注册

```http
POST /api/auth/register
```

**请求：**
```json
{
  "username": "newuser",
  "password": "password123",
  "captcha_id": "cap_1234567890_1234",
  "captcha_code": "ABCD"
}
```

### 获取当前用户

```http
GET /api/auth/me
Authorization: Bearer <token>
```

**响应：**
```json
{
  "id": 1,
  "username": "admin",
  "role": "super_admin",
  "department_id": 1,
  "department_name": "技术部",
  "nickname": "管理员",
  "email": "admin@example.com",
  "avatar_url": null
}
```

---

## 💬 对话接口

### 获取会话列表

```http
GET /api/chat/sessions
Authorization: Bearer <token>
```

**响应：**
```json
[
  {
    "id": 1,
    "name": "新对话",
    "user_id": 1
  }
]
```

### 创建会话

```http
POST /api/chat/sessions
Authorization: Bearer <token>
```

**请求：**
```json
{
  "name": "产品咨询"
}
```

### 流式问答

```http
POST /api/chat/stream
Authorization: Bearer <token>
Content-Type: application/json
```

**请求：**
```json
{
  "session_id": 1,
  "question": "什么是RAG？",
  "kb_ids": [1, 2],
  "model": "qwen-max",
  "temperature": 0.7,
  "top_p": 0.8,
  "max_tokens": 2048,
  "history_rounds": 5
}
```

**响应（SSE）：**
```
data: {"token": "RAG"}
data: {"token": "是"}
data: {"token": "检索"}
data: {"token": "增强"}
data: {"token": "生成"}
data: {"citations": [{"index": 1, "kb_id": 1, "document_id": 1, "chunk_id": 1}]}
data: [DONE]
```

### 导出对话

```http
GET /api/chat/sessions/{session_id}/export?format=markdown
Authorization: Bearer <token>
```

**参数：**
- `format`：导出格式，可选 `markdown` 或 `json`

---

## 📚 知识库接口

### 获取知识库列表

```http
GET /api/knowledge-bases
Authorization: Bearer <token>
```

**响应：**
```json
[
  {
    "id": 1,
    "name": "产品手册",
    "description": "产品使用说明",
    "department_id": 1,
    "is_public": true,
    "retrieval_type": "hybrid",
    "chunk_size": 500,
    "doc_count": 10,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### 创建知识库（管理员）

```http
POST /api/knowledge-bases
Authorization: Bearer <token>
```

**请求：**
```json
{
  "name": "新产品手册",
  "description": "新产品使用说明",
  "department_id": 1,
  "is_public": false,
  "retrieval_type": "hybrid",
  "chunk_size": 500,
  "chunk_overlap": 50,
  "parent_chunk_size": 2000
}
```

### 删除知识库（管理员）

```http
DELETE /api/knowledge-bases/{kb_id}
Authorization: Bearer <token>
```

---

## 📄 文档接口

### 获取文档列表

```http
GET /api/knowledge-bases/{kb_id}/documents
Authorization: Bearer <token>
```

**响应：**
```json
[
  {
    "id": 1,
    "kb_id": 1,
    "filename": "产品说明.pdf",
    "file_type": "pdf",
    "status": "completed",
    "chunk_count": 50,
    "version": 1,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### 上传文档（管理员）

```http
POST /api/knowledge-bases/{kb_id}/documents
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**参数：**
- `file`：文件（必填）
- `chunk_size`：切块大小（可选）
- `chunk_overlap`：重叠大小（可选）

### 查询解析进度

```http
GET /api/knowledge-bases/{kb_id}/documents/{document_id}/progress
Authorization: Bearer <token>
```

**响应：**
```json
{
  "progress": 75,
  "status": "parsing"
}
```

### 文档预览

```http
GET /api/knowledge-bases/{kb_id}/documents/{document_id}/preview
Authorization: Bearer <token>
```

**响应：**
- PDF：返回文件流
- 文本：返回纯文本内容

### 批量删除文档（管理员）

```http
POST /api/knowledge-bases/{kb_id}/documents/batch-delete
Authorization: Bearer <token>
```

**请求：**
```json
[1, 2, 3]
```

**响应：**
```json
{
  "message": "成功删除 3 个文档",
  "success_count": 3,
  "failed_count": 0,
  "failed_ids": []
}
```

### 获取文档块列表

```http
GET /api/knowledge-bases/{kb_id}/documents/{document_id}/chunks
Authorization: Bearer <token>
```

### 编辑文档块（管理员）

```http
PUT /api/chunks/{chunk_id}
Authorization: Bearer <token>
```

**请求：**
```json
{
  "content": "新的文档块内容"
}
```

---

## 🏢 部门接口

### 获取部门列表

```http
GET /api/departments
Authorization: Bearer <token>
```

### 创建部门（系统管理员）

```http
POST /api/departments
Authorization: Bearer <token>
```

**请求：**
```json
{
  "name": "新产品部"
}
```

---

## 👥 管理接口

### 获取用户列表（管理员）

```http
GET /api/admin/users
Authorization: Bearer <token>
```

### 创建用户（管理员）

```http
POST /api/admin/users
Authorization: Bearer <token>
```

**请求：**
```json
{
  "username": "newuser",
  "password": "password123",
  "role": "user",
  "department_id": 1
}
```

### 修改用户（管理员）

```http
PUT /api/admin/users/{user_id}
Authorization: Bearer <token>
```

### 重置密码（管理员）

```http
POST /api/admin/users/{user_id}/reset-password
Authorization: Bearer <token>
```

**请求：**
```json
{
  "new_password": "newpassword123"
}
```

---

## 🏥 系统接口

### 健康检查

```http
GET /health
```

**响应：**
```json
{
  "status": "ok"
}
```

### 深度健康检查

```http
GET /health/deep
```

**响应：**
```json
{
  "status": "ok",
  "checks": {
    "mysql": {"status": "ok"},
    "milvus": {"status": "ok"},
    "redis": {"status": "ok"}
  }
}
```

---

## 📊 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 413 | 文件过大 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

**错误响应格式：**
```json
{
  "detail": "错误描述信息"
}
```

---

## 💡 使用示例

### Python 示例

```python
import requests

# 登录
resp = requests.post("http://localhost:8000/api/auth/login", json={
    "username": "admin",
    "password": "admin123",
    "captcha_id": "...",
    "captcha_code": "..."
})
token = resp.json()["access_token"]

# 流式问答
headers = {"Authorization": f"Bearer {token}"}
resp = requests.post(
    "http://localhost:8000/api/chat/stream",
    json={
        "question": "什么是RAG？",
        "kb_ids": [1],
        "model": "qwen-max"
    },
    headers=headers,
    stream=True
)

for line in resp.iter_lines():
    if line:
        print(line.decode())
```

### JavaScript 示例

```javascript
// 登录
const loginResp = await fetch('/api/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    username: 'admin',
    password: 'admin123',
    captcha_id: '...',
    captcha_code: '...'
  })
});
const {access_token} = await loginResp.json();

// 流式问答
const resp = await fetch('/api/chat/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({
    question: '什么是RAG？',
    kb_ids: [1],
    model: 'qwen-max'
  })
});

const reader = resp.body.getReader();
while (true) {
  const {done, value} = await reader.read();
  if (done) break;
  console.log(new TextDecoder().decode(value));
}
```
