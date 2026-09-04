# 数据库设计

## 📋 概述

RAG 系统使用 MySQL 8.0 作为关系型数据库，存储用户、知识库、文档、对话等业务数据。

---

## 📊 数据库表结构

### 用户表 (users)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| username | VARCHAR(50) | 用户名，唯一 |
| password_hash | VARCHAR(255) | 密码哈希 |
| nickname | VARCHAR(50) | 昵称 |
| email | VARCHAR(100) | 邮箱 |
| avatar_url | VARCHAR(500) | 头像 URL |
| role | VARCHAR(20) | 角色：super_admin/dept_admin/user |
| department_id | INT | 所属部门 ID |
| is_active | BOOLEAN | 是否启用 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 部门表 (departments)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| name | VARCHAR(100) | 部门名称 |
| created_at | DATETIME | 创建时间 |

### 知识库表 (knowledge_bases)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| name | VARCHAR(100) | 知识库名称 |
| description | TEXT | 描述 |
| department_id | INT | 所属部门 ID |
| is_public | BOOLEAN | 是否公开 |
| retrieval_type | VARCHAR(20) | 检索类型：hybrid/dense |
| chunk_size | INT | 切块大小 |
| chunk_overlap | INT | 重叠大小 |
| parent_chunk_size | INT | 父块大小 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 文档表 (documents)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| kb_id | INT | 所属知识库 ID |
| filename | VARCHAR(255) | 文件名 |
| file_type | VARCHAR(20) | 文件类型 |
| file_path | VARCHAR(500) | 文件路径 |
| file_size | BIGINT | 文件大小 |
| chunk_count | INT | 文档块数量 |
| version | INT | 版本号 |
| status | VARCHAR(20) | 状态：pending/parsing/completed/failed |
| error_message | TEXT | 错误信息 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 文档块表 (chunks)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| document_id | INT | 所属文档 ID |
| content | TEXT | 文档块内容 |
| chunk_index | INT | 块索引 |
| version | INT | 版本号 |
| vector_id | VARCHAR(100) | Milvus 中的向量 ID |
| created_at | DATETIME | 创建时间 |

### 对话表 (chat_sessions)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| user_id | INT | 用户 ID |
| name | VARCHAR(100) | 会话名称 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 对话消息表 (chat_messages)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| session_id | INT | 会话 ID |
| role | VARCHAR(20) | 角色：user/assistant |
| content | TEXT | 消息内容 |
| citations | JSON | 引用信息 |
| created_at | DATETIME | 创建时间 |

---

## 🔗 ER 关系图

```
departments 1──N users
departments 1──N knowledge_bases
knowledge_bases 1──N documents
documents 1──N chunks
users 1──N chat_sessions
chat_sessions 1──N chat_messages
```

---

## 🔧 数据库配置

### 连接配置

**文件**：`app/database.py`

```python
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=20,
    max_overflow=10,
)
```

### 自动建表

```python
# config/settings.py
auto_create_tables: bool = True  # 开发环境可开启
```

---

## 📝 Alembic 迁移

```bash
# 创建迁移
uv run alembic revision --autogenerate -m "描述"

# 执行迁移
uv run alembic upgrade head

# 回滚
uv run alembic downgrade -1
```

---

## 📚 相关文档

- [技术架构](./architecture.md)
- [API 接口](./api-reference.md)
