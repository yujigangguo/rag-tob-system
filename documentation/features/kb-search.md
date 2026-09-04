# 知识库搜索功能

## 📋 功能说明

在知识库列表页面支持按**名称**和**描述**进行搜索，快速定位目标知识库。

---

## 🎯 使用方法

1. 点击左侧菜单"知识库"
2. 在页面顶部搜索框中输入关键词
3. 列表自动过滤显示匹配的知识库

### 搜索示例

| 输入 | 匹配结果 |
|------|----------|
| 产品 | 名称或描述中包含"产品"的知识库 |
| 手册 | 名称或描述中包含"手册"的知识库 |
| FAQ | 名称或描述中包含"FAQ"的知识库 |

---

## 🔍 搜索逻辑

```typescript
// 按名称和描述过滤
const filteredKbs = computed(() => {
  const keyword = searchKeyword.value.toLowerCase()
  if (!keyword) return knowledgeBases.value
  return knowledgeBases.value.filter(
    (kb) =>
      kb.name.toLowerCase().includes(keyword) ||
      (kb.description && kb.description.toLowerCase().includes(keyword))
  )
})
```

- 不区分大小写
- 支持部分匹配
- 同时搜索名称和描述

---

## 📚 相关文档

- [使用说明](../getting-started/user-guide.md)
