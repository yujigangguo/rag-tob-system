# 方案3：优化后的全 Docker 部署

## 📋 方案概述

使用 **优化后的 Docker Compose** 一键部署全部服务，通过配置优化减少卡顿。

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose                           │
├─────────────────────────────────────────────────────────────┤
│  frontend (Nginx)        │  backend (Gunicorn)              │
│  前端静态文件 + 反向代理  │  4 Worker 进程                   │
│  :8080                   │  :8000                           │
├─────────────────────────────────────────────────────────────┤
│  MySQL 8.0               │  Redis 7                         │
│  :3306                   │  :6379                           │
├─────────────────────────────────────────────────────────────┤
│  Milvus + etcd + MinIO                                      │
│  :19530                                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ 优点

- 🚀 **一键部署**：`docker compose up -d` 启动全部服务
- 📦 **环境隔离**：所有服务互不影响
- 🔄 **易于升级**：拉取代码后重新构建即可
- 💾 **数据持久化**：使用 Docker Volume 保存数据

## ⚠️ 缺点

- 🐢 **有一定性能损耗**：虚拟化层开销
- 💾 **资源占用较高**：每个容器都需要独立资源

---

## 🚀 快速部署

### 第一步：服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 重新登录
logout
```

### 第二步：克隆项目

```bash
cd /opt
git clone <你的仓库地址> rag-system
cd rag-system
```

### 第三步：配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
vim .env
```

修改以下配置：
```bash
# 必须修改的配置
SECRET_KEY=你的随机密钥
LLM_API_KEY=你的API密钥
EMBEDDING_API_KEY=你的API密钥

# 数据库密码（建议修改）
MYSQL_ROOT_PASSWORD=你的强密码
MYSQL_PASSWORD=你的强密码
DB_PASSWORD=你的强密码
REDIS_PASSWORD=你的强密码
```

### 第四步：创建优化的 docker-compose.yml

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # ================= Milvus 向量库 =================
  etcd:
    container_name: milvus-etcd
    restart: unless-stopped
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_ENABLE_V2=true
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
    volumes:
      - milvus_etcd:/etcd/data
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd/data
    network_mode: host
    deploy:
      resources:
        limits:
          memory: 512M

  minio:
    container_name: milvus-minio
    restart: unless-stopped
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY:-minioadmin}
      MINIO_SECRET_KEY: ${MINIO_SECRET_KEY:-minioadmin}
    volumes:
      - milvus_minio:/minio/data
    command: minio server /minio/data
    network_mode: host
    deploy:
      resources:
        limits:
          memory: 512M

  redis:
    container_name: milvus-redis
    restart: unless-stopped
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - milvus_redis:/data
    command: redis-server --requirepass ${REDIS_PASSWORD:-1234}
    deploy:
      resources:
        limits:
          memory: 256M

  milvus:
    container_name: milvus-standalone
    restart: unless-stopped
    image: milvusdb/milvus:v2.4.4
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: localhost:2379
      MINIO_ADDRESS: localhost:9000
    ports:
      - "19530:19530"
      - "9091:9091"
    volumes:
      - milvus_data:/var/lib/milvus
    depends_on:
      - etcd
      - minio
    network_mode: host
    deploy:
      resources:
        limits:
          memory: 2G

  # ================= MySQL =================
  mysql:
    image: mysql:8.0
    container_name: rag-mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-root123456}
      MYSQL_DATABASE: ${DB_NAME:-rag_db}
      MYSQL_USER: ${DB_USER:-rag_user}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD:-rag_pass123}
      TZ: Asia/Shanghai
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    command:
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
      - --default-authentication-plugin=mysql_native_password
      - --innodb-buffer-pool-size=1G
      - --max-connections=200
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 12
    deploy:
      resources:
        limits:
          memory: 2G

  # ================= 后端 =================
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: rag-backend
    restart: unless-stopped
    depends_on:
      mysql:
        condition: service_healthy
      milvus:
        condition: service_started
      redis:
        condition: service_started
    environment:
      DB_HOST: mysql
      DB_PORT: 3306
      DB_USER: ${DB_USER:-rag_user}
      DB_PASSWORD: ${MYSQL_PASSWORD:-rag_pass123}
      DB_NAME: ${DB_NAME:-rag_db}
      MILVUS_URI: http://localhost:19530
      MILVUS_TOKEN: ${MILVUS_TOKEN:-}
      LLM_API_KEY: ${LLM_API_KEY:-}
      LLM_BASE_URL: ${LLM_BASE_URL:-https://dashscope.aliyuncs.com/compatible-mode/v1}
      LLM_MODEL: ${LLM_MODEL:-qwen-max}
      EMBEDDING_API_KEY: ${EMBEDDING_API_KEY:-}
      EMBEDDING_MODEL: ${EMBEDDING_MODEL:-text-embedding-v3}
      EMBEDDING_DIM: ${EMBEDDING_DIM:-1024}
      SECRET_KEY: ${SECRET_KEY:-change-me-in-production-please}
      RUN_MIGRATIONS: ${RUN_MIGRATIONS:-true}
      REDIS_URL: redis://:${REDIS_PASSWORD:-1234}@localhost:6379/0
      GUNICORN_WORKERS: ${GUNICORN_WORKERS:-4}
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    network_mode: host
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G

  # ================= 前端 =================
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: rag-frontend
    restart: unless-stopped
    depends_on:
      - backend
    ports:
      - "8080:80"
    deploy:
      resources:
        limits:
          memory: 256M

volumes:
  milvus_etcd:
  milvus_minio:
  milvus_redis:
  milvus_data:
  mysql_data:
EOF
```

### 第五步：启动服务

```bash
# 构建并启动
docker compose up -d --build

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 第六步：验证部署

```bash
# 检查所有服务状态
docker compose ps

# 测试后端 API
curl http://localhost:8000/health
curl http://localhost:8000/health/deep

# 访问前端
curl http://localhost:8080
```

---

## 🔧 优化配置详解

### 1. 资源限制

```yaml
deploy:
  resources:
    limits:
      cpus: '4'      # 最多使用 4 个 CPU 核心
      memory: 4G     # 最多使用 4GB 内存
    reservations:
      cpus: '1'      # 预留 1 个 CPU 核心
      memory: 1G     # 预留 1GB 内存
```

### 2. 网络模式

```yaml
network_mode: host  # 使用主机网络，减少网络开销
```

**说明**：
- `host` 模式：容器直接使用主机网络，性能最好
- 默认 `bridge` 模式：容器有独立网络，有额外开销

### 3. Volume 优化

```yaml
volumes:
  mysql_data:      # 使用命名 Volume，性能优于绑定挂载
    driver: local
```

### 4. 日志限制

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"   # 单个日志文件最大 10MB
    max-file: "3"     # 最多保留 3 个日志文件
```

---

## 📊 性能对比

| 配置 | 启动时间 | API 响应 | 内存占用 |
|------|----------|----------|----------|
| 默认 Docker | 较慢 | 较慢 | 较高 |
| 优化后 Docker | 较快 | 较快 | 适中 |
| 原生部署 | 最快 | 最快 | 最低 |

---

## 🔄 日常运维

### 代码更新

```bash
cd /opt/rag-system

# 拉取最新代码
git pull

# 重新构建并启动
docker compose up -d --build

# 或者只重启后端
docker compose up -d --build backend
```

### 数据备份

```bash
# 备份 MySQL
docker exec rag-mysql mysqldump -u root -p${MYSQL_ROOT_PASSWORD} rag_db \
    > backup_$(date +%Y%m%d).sql

# 备份所有 Docker Volume
docker run --rm -v rag-system_mysql_data:/data -v $(pwd):/backup \
    alpine tar czf /backup/mysql_volume_$(date +%Y%m%d).tar.gz /data
```

### 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f mysql
docker compose logs -f milvus
```

### 重启服务

```bash
# 重启所有服务
docker compose restart

# 重启特定服务
docker compose restart backend
docker compose restart mysql
```

### 清理资源

```bash
# 清理未使用的镜像
docker image prune -a

# 清理未使用的 Volume（谨慎！）
docker volume prune

# 清理所有未使用资源
docker system prune -a
```

---

## 🐛 常见问题

### Q1: 构建很慢

```bash
# 使用 BuildKit 加速
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# 使用离线包
./docker-prebuild.sh
docker compose up -d --build
```

### Q2: 容器启动失败

```bash
# 查看详细日志
docker compose logs backend

# 检查资源使用
docker stats

# 进入容器调试
docker exec -it rag-backend /bin/bash
```

### Q3: 内存不足

```bash
# 查看内存使用
docker stats --no-stream

# 减小资源限制
# 编辑 docker-compose.yml，减小 memory 值

# 或者添加 swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Q4: 磁盘空间不足

```bash
# 查看磁盘使用
df -h

# 清理 Docker 资源
docker system prune -a

# 清理旧日志
sudo journalctl --vacuum-time=7d
```

---

## 📁 文件结构

```
/opt/rag-system/
├── app/                    # 后端代码
├── config/                 # 配置文件
├── frontend/               # 前端代码
├── data/                   # 数据目录（挂载）
├── scripts/                # 脚本
├── .env                    # 环境变量
├── docker-compose.yml      # Docker Compose 配置
├── Dockerfile              # 后端镜像配置
└── pyproject.toml          # Python 依赖
```

---

## 🔗 相关文档

- [优化方案文档](../docs/optimization-plan.md)
- [备份脚本](../scripts/backup.sh)
- [健康检查脚本](../scripts/healthcheck.sh)
