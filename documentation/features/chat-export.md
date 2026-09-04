# 对话导出功能

## 📋 功能说明

支持将对话记录导出为 **Markdown** 和 **JSON** 两种格式。

---

## 🎯 使用方法

### 操作步骤

1. 在左侧会话列表中，鼠标悬停到目标会话
2. 点击"更多"按钮（三个点）
3. 选择"导出 Markdown"或"导出 JSON"
4. 文件将自动下载

### 导出格式

#### Markdown 格式

```markdown
# 对话记录：产品咨询

**导出时间**：2024-01-01 12:00:00

---

## 第 1 轮

**用户**：什么是 RAG？

**助手**：RAG（检索增强生成）是一种技术...

> **参考来源**：
> - 知识库：产品手册
> - 文档：产品说明.pdf
> - 引用：RAG是一种结合了信息检索和大语言模型的技术...

---

## 第 2 轮

**用户**：它有什么优势？

**助手**：RAG 的主要优势包括...
```

#### JSON 格式

```json
{
  "session_name": "产品咨询",
  "export_time": "2024-01-01T12:00:00",
  "messages": [
    {
      "role": "user",
      "content": "什么是 RAG？",
      "created_at": "2024-01-01T12:00:00"
    },
    {
      "role": "assistant",
      "content": "RAG（检索增强生成）是一种技术...",
      "citations": [
        {
          "index": 1,
          "kb_id": 1,
          "document_id": 1,
          "chunk_id": 1
        }
      ],
      "created_at": "2024-01-01T12:00:01"
    }
  ]
}
```

---

## 🔧 API 接口

```http
GET /api/chat/sessions/{session_id}/export?format=markdown
Authorization: Bearer <token>
```

**参数：**
- `format`：导出格式，可选 `markdown` 或 `json`

**响应：**
- Content-Type: `application/octet-stream`
- 自动触发浏览器下载

---

## 💡 使用场景

| 场景 | 推荐格式 |
|------|----------|
| 阅读和分享 | Markdown |
| 数据分析 | JSON |
| 二次开发 | JSON |
| 存档备份 | 两者均可 |

---

## 📚 相关文档

- [使用说明](../getting-started/user-guide.md)
- [API 接口](../technical/api-reference.md)
