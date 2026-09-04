# 增量更新与版本管理

## 📋 概述

支持文档的增量更新和版本管理，可以查看历史版本并回滚。

---

## 🎯 功能特性

- ✅ 文档版本自动递增
- ✅ 查看历史版本列表
- ✅ 查看指定版本内容
- ✅ 回滚到上一版本
- ✅ 版本对比

---

## 🔄 更新流程

```
上传文档 v1
    │
    ▼
解析完成，生成向量
    │
    ▼
重新上传同名文档
    │
    ▼
自动创建 v2
    │
    ├── 保留 v1 的数据
    └── 生成 v2 的向量
    │
    ▼
如需回滚，恢复 v1
```

---

## 🎯 使用方法

### 查看版本历史

1. 进入知识库详情页
2. 点击文档旁的版本号（如 `v2`）
3. 弹窗显示版本历史列表

### 回滚版本

1. 在版本历史弹窗中
2. 点击"回滚到上一版本"
3. 确认回滚

---

## 🔧 API 接口

### 获取版本列表

```http
GET /api/knowledge-bases/{kb_id}/documents/{document_id}/versions
```

### 获取指定版本内容

```http
GET /api/knowledge-bases/{kb_id}/documents/{document_id}/versions/{version}/chunks
```

### 回滚到上一版本

```http
POST /api/knowledge-bases/{kb_id}/documents/{document_id}/rollback
```

---

## 📊 版本数据结构

```json
{
  "id": 1,
  "document_id": 1,
  "version": 2,
  "chunk_count": 50,
  "created_at": "2024-01-01T12:00:00"
}
```

---

## ⚠️ 注意事项

- 回滚操作**不可恢复**当前版本
- 回滚后会重新生成向量索引
- 只有**管理员**可以执行回滚操作

---

## 📚 相关文档

- [使用说明](../getting-started/user-guide.md)
- [API 接口](../technical/api-reference.md)
