# 代码规范

## 📋 Python 代码规范

### 工具配置

```toml
# pyproject.toml
[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
```

### 命名规范

```python
# 模块名：小写下划线
user_service.py

# 类名：大驼峰
class UserService:
    pass

# 函数名：小写下划线
def get_user_by_id(user_id: int) -> User:
    pass

# 常量：大写下划线
MAX_RETRY_COUNT = 3
```

### 类型注解

```python
def process_document(
    file_path: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Chunk]:
    """处理文档并返回文档块列表。"""
    pass
```

### 文档字符串

```python
def search(query: str, kb_ids: List[int], top_k: int = 5) -> List[SearchResult]:
    """在知识库中搜索相关内容。
    
    Args:
        query: 搜索查询
        kb_ids: 知识库 ID 列表
        top_k: 返回结果数量
        
    Returns:
        搜索结果列表
        
    Raises:
        ValueError: 知识库不存在时抛出
    """
    pass
```

---

## 📋 TypeScript/Vue 代码规范

### 工具配置

```json
// .eslintrc.json
{
  "extends": [
    "eslint:recommended",
    "@vue/eslint-config-typescript"
  ]
}
```

### 命名规范

```typescript
// 文件名：大驼峰
UserService.ts

// 接口：大驼峰，I 前缀可选
interface User {
  id: number;
  username: string;
}

// 函数：小驼峰
function getUserById(id: number): Promise<User> {
  // ...
}

// 常量：大写下划线
const MAX_RETRY_COUNT = 3;
```

### Vue 组件

```vue
<script setup lang="ts">
// 使用 Composition API
import { ref, computed } from 'vue'

const count = ref(0)
const doubled = computed(() => count.value * 2)
</script>
```

---

## 📁 文件结构

```
app/
├── api/                # API 路由
│   ├── __init__.py
│   ├── auth.py
│   └── chat.py
├── models/             # 数据库模型
│   ├── __init__.py
│   └── user.py
├── services/           # 业务逻辑
│   ├── __init__.py
│   └── auth_service.py
└── rag/                # RAG 核心
    ├── __init__.py
    ├── retrieval.py
    └── embeddings.py
```

---

## 📚 相关文档

- [开发指南](./setup.md)
