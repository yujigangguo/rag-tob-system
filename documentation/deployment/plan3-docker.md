# Docker 全容器部署

## 📋 方案概述

使用 **优化后的 Docker Compose** 一键部署全部服务。

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose                           │
├─────────────────────────────────────────────────────────────┤
│  frontend (Nginx)        │  backend (Gunicorn)              │
│  :8080                   │  :8000                           │
├─────────────────────────────────────────────────────────────┤
│  MySQL 8.0               │  Redis 7                         │
├─────────────────────────────────────────────────────────────┤
│  Milvus + etcd + MinIO                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ 优点

- 🚀 **一键部署**：`docker compose up -d` 启动全部
- 📦 **环境隔离**：所有服务互不影响
- 🔄 **易于升级**：重新构建即可

## ⚠️ 缺点

- 🐢 **有一定性能损耗**：虚拟化层开销
- 💾 **资源占用较高**

---

## 🚀 快速部署

### 第一步：准备

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 克隆项目
git clone <仓库地址> cd RAG
```

### 第二步：配置环境变量

```bash
cp .env.example .env
vim .env
```

**必须修改：**
```bash
LLM_API_KEY=你的API密钥
EMBEDDING_API_KEY=你的API密钥
SECRET_KEY=随机字符串
```

### 第三步：启动

```bash
docker compose up -d --build
```

### 第四步：访问

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:8080 |
| 后端 API | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health/deep |

---

## 🔧 常用命令

```bash
# 查看状态
docker compose ps

# 查看日志
docker compose logs -f

# 停止服务
docker compose down

# 重新构建
docker compose up -d --build
```

---

## 📊 资源配置

编辑 `docker-compose.yml`，按需调整：

```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
```

---

## ❓ 常见问题

### Q1: 构建很慢

参考 [Docker 镜像优化](./docker-mirrors.md) 配置国内镜像源。

### Q2: 内存不足

```bash
# 添加 swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 📁 相关文档

- [Docker 镜像优化](./docker-mirrors.md)
- [生产环境部署](./plan2-prod-hybrid.md)
