# 方案1：开发环境混合部署

## 📋 方案概述

在 Windows 开发环境中，使用 **Docker 运行数据库服务**，**原生运行应用代码**，兼顾便利性和开发效率。

```
┌─────────────────────────────────────────────────────────────┐
│                    Windows 开发环境                          │
├─────────────────────────────────────────────────────────────┤
│  终端1: npm run dev                                         │
│  前端开发服务器（Vite 热更新）                                │
│  http://localhost:5173                                       │
├─────────────────────────────────────────────────────────────┤
│  终端2: uv run uvicorn app.main:app --reload                │
│  后端开发服务器（代码热重载）                                 │
│  http://localhost:8000                                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Docker Desktop                                         ││
│  │  ┌──────────┐ ┌──────────┐ ┌─────────────────────────┐ ││
│  │  │  MySQL   │ │  Redis   │ │  Milvus + etcd + MinIO  │ ││
│  │  │  8.0     │ │  latest  │ │  v2.4.4                 │ ││
│  │  │  :3306   │ │  :6379   │ │  :19530                 │ ││
│  │  └──────────┘ └──────────┘ └─────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ 优点

- 🚀 **后端热重载**：修改代码自动重启，开发效率高
- 🚀 **前端热更新**：Vite HMR，秒级刷新
- 🔍 **调试方便**：可直接打断点、查看日志
- 📦 **数据库隔离**：Docker 管理，数据不丢失，易清理

---

## 📋 前置条件

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.11+ | 推荐使用 uv 管理 |
| Node.js | 18+ | 前端构建 |
| Docker Desktop | 最新版 | 运行数据库服务 |
| Git | 最新版 | 代码管理 |

---

## 🚀 快速启动

### 第一步：启动数据库服务

```bash
# 在项目根目录执行
docker compose up -d mysql redis milvus
```

等待服务启动完成（约 30 秒），检查状态：

```bash
docker compose ps
```

应该看到：
```
NAME                STATUS
milvus-etcd         Up
milvus-minio        Up
milvus-redis        Up
milvus-standalone   Up
rag-mysql           Up (healthy)
```

### 第二步：配置环境变量

复制并修改 `.env` 文件：

```bash
# 确保以下配置正确
DB_HOST=localhost
DB_PORT=3306
DB_USER=rag_user
DB_PASSWORD=rag_pass123
DB_NAME=rag_db

REDIS_URL=redis://:1234@localhost:6379/0

MILVUS_URI=http://localhost:19530

LLM_API_KEY=你的API密钥
EMBEDDING_API_KEY=你的API密钥
```

### 第三步：启动后端

```bash
# 安装依赖（首次）
pip install uv
uv sync

# 启动后端（热重载模式）
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端启动成功会显示：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### 第四步：启动前端

```bash
# 新开一个终端
cd frontend

# 安装依赖（首次）
npm install

# 启动前端开发服务器
npm run dev
```

前端启动成功会显示：
```
  VITE v6.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
```

### 第五步：访问系统

- **前端页面**：http://localhost:5173
- **后端 API 文档**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health/deep

---

## 🔧 常用命令

### 数据库管理

```bash
# 启动数据库服务
docker compose up -d mysql redis milvus

# 停止数据库服务
docker compose down

# 停止并删除数据（谨慎！会清空数据）
docker compose down -v

# 查看日志
docker compose logs -f mysql
docker compose logs -f milvus

# 进入 MySQL 命令行
docker exec -it rag-mysql mysql -u rag_user -p rag_db
```

### 后端开发

```bash
# 启动后端（热重载）
uv run uvicorn app.main:app --reload

# 运行数据库迁移
uv run alembic upgrade head

# 创建新的数据库迁移
uv run alembic revision --autogenerate -m "描述"

# 运行测试
uv run pytest
```

### 前端开发

```bash
cd frontend

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

---

## 🐛 常见问题

### Q1: 端口被占用

```bash
# 查看端口占用
netstat -ano | findstr :3306
netstat -ano | findstr :8000
netstat -ano | findstr :5173

# 杀掉占用端口的进程
taskkill /PID <进程ID> /F
```

### Q2: Docker 容器启动失败

```bash
# 查看容器日志
docker compose logs mysql
docker compose logs milvus

# 重启容器
docker compose restart mysql
```

### Q3: 后端连接数据库失败

检查 `.env` 配置：
```bash
# 确保使用 localhost，不是 127.0.0.1
DB_HOST=localhost

# 确保 Redis URL 正确
REDIS_URL=redis://:1234@localhost:6379/0
```

### Q4: 前端请求后端 404

检查前端代理配置 `frontend/vite.config.ts`：
```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

---

## 📁 相关文件

| 文件 | 说明 |
|------|------|
| `docker-compose.yml` | 数据库服务配置 |
| `.env` | 环境变量配置 |
| `pyproject.toml` | Python 依赖 |
| `frontend/package.json` | 前端依赖 |

---

## 🔄 数据备份

```bash
# 备份 MySQL
docker exec rag-mysql mysqldump -u root -p rag_db > backup_$(date +%Y%m%d).sql

# 备份 Milvus 数据
docker exec milvus-standalone tar -czf /tmp/milvus.tar.gz /var/lib/milvus
docker cp milvus-standalone:/tmp/milvus.tar.gz ./milvus_backup_$(date +%Y%m%d).tar.gz
```
