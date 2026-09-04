# 快速部署指南

## 🚀 5 分钟快速开始

本指南帮助你快速部署 RAG 知识问答系统。

---

## 📋 前置条件

| 软件 | 版本 | 说明 |
|------|------|------|
| Docker | 最新 | 容器运行环境 |
| Docker Compose | 最新 | 容器编排工具 |
| Git | 最新 | 代码管理 |

---

## 🎯 方案选择

| 方案 | 适用场景 | 命令 |
|------|----------|------|
| **全 Docker** | 快速体验、演示 | `docker compose up -d` |
| **开发环境** | 本地开发调试 | 见 [开发环境部署](../deployment/plan1-dev-hybrid.md) |
| **生产环境** | 上线部署 | 见 [生产环境部署](../deployment/plan2-prod-hybrid.md) |

---

## 📦 全 Docker 部署（最快）

### 第一步：克隆项目

```bash
git clone <仓库地址>
cd RAG
```

### 第二步：配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置（必须修改）
vim .env
```

**必须修改的配置：**
```bash
# API 密钥（必填）
LLM_API_KEY=你的通义千问API密钥
EMBEDDING_API_KEY=你的通义千问API密钥

# 安全密钥（建议修改）
SECRET_KEY=随机字符串
```

### 第三步：启动服务

```bash
# 构建并启动（首次较慢）
docker compose up -d --build

# 查看状态
docker compose ps
```

### 第四步：访问系统

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端页面 | http://localhost:8080 | 用户界面 |
| 后端 API | http://localhost:8000/docs | API 文档 |
| 健康检查 | http://localhost:8000/health/deep | 系统状态 |

### 第五步：登录系统

默认管理员账号：
- 用户名：`admin`
- 密码：`admin123`

> ⚠️ 首次登录后请立即修改密码！

---

## 🔧 常用命令

```bash
# 查看日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 重新构建
docker compose up -d --build
```

---

## ❓ 常见问题

### Q1: 构建很慢怎么办？

配置国内镜像源：
```bash
# 参考 Docker 镜像优化文档
./check-mirrors.sh
```

### Q2: 启动失败怎么办？

```bash
# 查看详细日志
docker compose logs backend

# 检查健康状态
curl http://localhost:8000/health/deep
```

### Q3: 如何配置 API 密钥？

编辑 `.env` 文件：
```bash
LLM_API_KEY=你的密钥
EMBEDDING_API_KEY=你的密钥
```

---

## 📚 下一步

- [使用说明](./user-guide.md) - 了解系统功能
- [生产环境部署](../deployment/plan2-prod-hybrid.md) - 部署到服务器
- [性能优化](../optimization/performance.md) - 优化系统性能
