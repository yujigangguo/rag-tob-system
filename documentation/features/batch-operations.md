# 批量操作功能

## 📋 功能说明

支持在知识库详情页**批量选择并删除**文档，提高管理效率。

---

## 🎯 使用方法

### 操作步骤

1. 进入知识库详情页
2. 勾选要删除的文档（支持全选）
3. 点击"删除(N)"按钮
4. 确认删除

### 界面说明

```
┌─────────────────────────────────────┐
│ 文档列表(10)              ☑ 全选    │
├─────────────────────────────────────┤
│ ☑ 📄 产品说明.pdf      [删除(3)]   │
│ ☑ 📄 员工手册.md                    │
│ ☑ 📄 常见问题FAQ.md                 │
│ ☐ 📄 培训资料.pptx                  │
│ ...                                 │
└─────────────────────────────────────┘
```

---

## 🔧 API 接口

```http
POST /api/knowledge-bases/{kb_id}/documents/batch-delete
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体：**
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

---

## ⚠️ 注意事项

- 只有**管理员**可以使用批量删除功能
- 删除操作**不可恢复**
- 删除文档会同时删除相关的向量数据

---

## 📚 相关文档

- [使用说明](../getting-started/user-guide.md)
- [API 接口](../technical/api-reference.md)
