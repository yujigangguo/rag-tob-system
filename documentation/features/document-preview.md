# 文档预览功能

## 📋 功能说明

支持在网页中直接预览上传的文档，无需下载。

---

## 🎯 支持格式

| 格式 | 预览方式 | 说明 |
|------|----------|------|
| PDF | 新窗口打开 | 使用浏览器内置 PDF 阅读器 |
| TXT/Markdown | 弹窗显示 | 解析后显示文本内容 |
| Word (.docx) | 弹窗显示 | 解析后显示文本内容 |
| PPT (.pptx) | 弹窗显示 | 解析后显示文本内容 |

---

## 🎯 使用方法

1. 进入知识库详情页
2. 在文档列表中找到目标文档
3. 点击"预览"按钮
4. 查看文档内容

---

## 🔧 API 接口

```http
GET /api/knowledge-bases/{kb_id}/documents/{document_id}/preview
Authorization: Bearer <token>
```

**响应：**
- PDF：返回 `application/pdf` 文件流
- 文本：返回 `text/plain` 解析后的内容

---

## 📚 相关文档

- [使用说明](../getting-started/user-guide.md)
- [API 接口](../technical/api-reference.md)
