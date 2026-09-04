# 开发环境搭建

## 📋 概述

本文档介绍如何搭建 RAG 知识问答系统的开发环境。

---

## 🎯 前置条件

| 软件 | 版本 | 说明 |
|------|------|------|
| Python | 3.11+ | 后端开发 |
| Node.js | 18+ | 前端开发 |
| Docker | 最新 | 运行数据库 |
| Git | 最新 | 代码管理 |
| VS Code | 最新 | 推荐编辑器 |

---

## 🚀 快速搭建

### 第一步：克隆项目

```bash
git clone <仓库地址>
cd RAG
```

### 第二步：启动数据库

```bash
docker compose up -d mysql redis milvus
```

### 第三步：配置后端

```bash
# 安装 uv（Python 包管理器）
pip install uv

# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env，配置 API 密钥等

# 运行数据库迁移
uv run alembic upgrade head

# 启动后端（热重载模式）
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 第四步：配置前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 第五步：访问系统

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000/docs

---

## 🛠️ 开发工具

### VS Code 插件推荐

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "Vue.volar"
  ]
}
```

### VS Code 配置

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  }
}
```

---

## 📁 项目结构

```
RAG/
├── app/                    # 后端代码
│   ├── api/                # API 路由
│   ├── models/             # 数据库模型
│   ├── services/           # 业务逻辑
│   ├── rag/                # RAG 核心
│   ├── schemas/            # Pydantic 模型
│   └── main.py             # 入口文件
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── api/            # API 调用
│   │   ├── stores/         # 状态管理
│   │   └── router/         # 路由配置
│   └── package.json
├── config/                 # 配置文件
├── tests/                  # 测试文件
├── alembic/                # 数据库迁移
├── docker-compose.yml      # Docker 配置
├── pyproject.toml          # Python 依赖
└── .env                    # 环境变量
```

---

## 🔧 常用命令

### 后端命令

```bash
# 启动开发服务器
uv run uvicorn app.main:app --reload

# 运行测试
uv run pytest

# 代码格式化
uv run ruff format .

# 代码检查
uv run ruff check .

# 创建数据库迁移
uv run alembic revision --autogenerate -m "描述"

# 运行数据库迁移
uv run alembic upgrade head

# 回滚数据库迁移
uv run alembic downgrade -1
```

### 前端命令

```bash
cd frontend

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 代码检查
npm run lint

# 代码格式化
npm run format
```

### Docker 命令

```bash
# 启动数据库服务
docker compose up -d mysql redis milvus

# 停止所有服务
docker compose down

# 查看日志
docker compose logs -f mysql

# 进入容器
docker exec -it rag-mysql mysql -u root -p
```

---

## 🐛 调试技巧

### 后端调试

```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或使用 VS Code 调试器
# 在 .vscode/launch.json 中配置
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": ["app.main:app", "--reload"],
            "jinja": true
        }
    ]
}
```

### 前端调试

```javascript
// 在代码中添加断点
debugger;

// 使用 Vue Devtools
// 安装浏览器插件
```

### 查看日志

```bash
# 后端日志
tail -f data/logs/app.log

# 数据库日志
docker compose logs -f mysql
```

---

## 📝 代码规范

### Python 代码规范

- 使用 Ruff 格式化代码
- 遵循 PEP 8 规范
- 使用类型注解
- 编写文档字符串

```python
def get_user(user_id: int) -> User:
    """获取用户信息。
    
    Args:
        user_id: 用户 ID
        
    Returns:
        User 对象
        
    Raises:
        HTTPException: 用户不存在时抛出 404
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user
```

### TypeScript 代码规范

- 使用 ESLint 检查代码
- 使用 Prettier 格式化代码
- 使用 TypeScript 类型定义

```typescript
interface User {
  id: number;
  username: string;
  role: 'super_admin' | 'dept_admin' | 'user';
}

async function getUser(id: number): Promise<User> {
  const response = await http.get(`/users/${id}`);
  return response.data;
}
```

---

## 🧪 测试

### 运行后端测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_auth.py

# 运行并显示覆盖率
uv run pytest --cov=app
```

### 编写测试

```python
# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login():
    response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

---

## ❓ 常见问题

### Q1: 依赖安装失败

```bash
# 清除缓存
uv cache clean

# 重新安装
uv sync --reinstall
```

### Q2: 数据库连接失败

```bash
# 检查 Docker 容器状态
docker compose ps

# 检查数据库日志
docker compose logs mysql
```

### Q3: 前端启动失败

```bash
# 清除依赖
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

---

## 📚 相关文档

- [代码规范](./code-style.md)
- [Alembic 迁移](./alembic.md)
- [API 文档](../technical/api-reference.md)
