# 生产环境部署（推荐）

## 📋 方案概述

在 Linux 服务器上，**应用层原生运行**，**数据库层使用 Docker**，兼顾性能和易维护性。

```
┌─────────────────────────────────────────────────────────────┐
│                      Linux 服务器                            │
├─────────────────────────────────────────────────────────────┤
│  Nginx (原生)                                                │
│  ├── 前端静态文件托管                                        │
│  ├── 反向代理后端 API                                        │
│  └── Gzip 压缩、缓存、限流                                   │
├─────────────────────────────────────────────────────────────┤
│  Python + Gunicorn (原生)                                    │
│  └── 4 Worker 进程                                           │
├─────────────────────────────────────────────────────────────┤
│  Docker (仅数据库)                                           │
│  ├── MySQL 8.0                                               │
│  ├── Redis 7                                                 │
│  └── Milvus + etcd + MinIO                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ 优点

- 🚀 **应用性能最优**：Python/Nginx 原生运行
- 🔍 **调试方便**：日志、进程直接查看
- 📦 **数据库隔离**：Docker 管理，升级备份简单
- 🔧 **精细调优**：可针对各组件单独优化

---

## 📋 前置条件

| 软件 | 版本 | 安装命令 |
|------|------|----------|
| Ubuntu | 22.04 LTS | - |
| Python | 3.11+ | `sudo apt install python3.11` |
| Node.js | 18+ | `curl -fsSL https://deb.nodesource.com/setup_18.x \| sudo -E bash -` |
| Docker | 最新 | `curl -fsSL https://get.docker.com \| sh` |
| Nginx | 最新 | `sudo apt install nginx` |

---

## 🚀 部署步骤

### 第一步：服务器初始化

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y git curl wget vim

# 安装 Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# 安装 Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Nginx
sudo apt install -y nginx

# 重新登录
logout
```

### 第二步：克隆项目

```bash
cd /opt
sudo mkdir rag-system
sudo chown $USER:$USER rag-system
cd rag-system
git clone <仓库地址> .
```

### 第三步：启动数据库

```bash
# 创建数据目录
mkdir -p volumes/{etcd,minio,milvus,redis,mysql}

# 创建数据库配置
cat > docker-compose-db.yml << 'EOF'
version: '3.8'

services:
  etcd:
    container_name: milvus-etcd
    restart: unless-stopped
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_ENABLE_V2=true
    volumes:
      - ./volumes/etcd:/etcd/data
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd/data
    network_mode: host

  minio:
    container_name: milvus-minio
    restart: unless-stopped
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - ./volumes/minio:/minio/data
    command: minio server /minio/data
    network_mode: host

  redis:
    container_name: milvus-redis
    restart: unless-stopped
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - ./volumes/redis:/data
    command: redis-server --requirepass 1234

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
    volumes:
      - ./volumes/milvus:/var/lib/milvus
    depends_on:
      - etcd
      - minio
    network_mode: host

  mysql:
    image: mysql:8.0
    container_name: rag-mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-root123456}
      MYSQL_DATABASE: rag_db
      MYSQL_USER: rag_user
      MYSQL_PASSWORD: ${MYSQL_PASSWORD:-rag_pass123}
      TZ: Asia/Shanghai
    ports:
      - "3306:3306"
    volumes:
      - ./volumes/mysql:/var/lib/mysql
    command:
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
      - --default-authentication-plugin=mysql_native_password
      - --innodb-buffer-pool-size=1G
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 12
EOF

# 启动数据库
docker compose -f docker-compose-db.yml up -d
```

### 第四步：配置环境变量

```bash
cat > .env << 'EOF'
# 应用配置
SECRET_KEY=$(openssl rand -hex 32)
LOG_LEVEL=INFO

# MySQL
DB_HOST=localhost
DB_PORT=3306
DB_USER=rag_user
DB_PASSWORD=rag_pass123
DB_NAME=rag_db

# Redis
REDIS_URL=redis://:1234@localhost:6379/0

# Milvus
MILVUS_URI=http://localhost:19530

# 大模型（必填）
LLM_API_KEY=你的API密钥
EMBEDDING_API_KEY=你的API密钥

# 数据库迁移
RUN_MIGRATIONS=true
AUTO_CREATE_TABLES=false
EOF

# 生成随机密钥
sed -i "s/\$(openssl rand -hex 32)/$(openssl rand -hex 32)/" .env
```

### 第五步：安装后端依赖

```bash
pip install uv
uv sync
uv run alembic upgrade head
```

### 第六步：构建前端

```bash
cd frontend
npm install
npm run build
sudo mkdir -p /var/www/rag-frontend
sudo cp -r dist/* /var/www/rag-frontend/
sudo chown -R www-data:www-data /var/www/rag-frontend
cd ..
```

### 第七步：配置 Nginx

```bash
sudo cat > /etc/nginx/sites-available/rag-system << 'EOF'
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    listen 80;
    server_name your-domain.com;

    # Gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # 前端
    root /var/www/rag-frontend;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API 代理
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_buffering off;
        proxy_read_timeout 300s;
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    client_max_body_size 10m;
}
EOF

sudo ln -sf /etc/nginx/sites-available/rag-system /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 第八步：配置 systemd 服务

```bash
sudo cat > /etc/systemd/system/rag-backend.service << 'EOF'
[Unit]
Description=RAG System Backend
After=network.target docker.service

[Service]
Type=exec
User=root
WorkingDirectory=/opt/rag-system
Environment="PATH=/opt/rag-system/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/rag-system/.venv/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 300
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable rag-backend
sudo systemctl start rag-backend
```

### 第九步：验证部署

```bash
# 检查服务状态
docker compose -f docker-compose-db.yml ps
sudo systemctl status rag-backend
sudo systemctl status nginx

# 测试 API
curl http://localhost/health
curl http://localhost/health/deep
```

---

## 🔧 日常运维

### 代码更新

```bash
cd /opt/rag-system
git pull
uv sync
uv run alembic upgrade head
sudo systemctl restart rag-backend

cd frontend
npm install
npm run build
sudo cp -r dist/* /var/www/rag-frontend/
```

### 查看日志

```bash
# 后端日志
sudo journalctl -u rag-backend -f
sudo tail -f /var/log/rag-backend/access.log

# 数据库日志
docker compose -f docker-compose-db.yml logs -f
```

### 数据备份

```bash
# 备份 MySQL
docker exec rag-mysql mysqldump -u root -p rag_db > backup_$(date +%Y%m%d).sql

# 备份 Milvus
docker exec milvus-standalone tar -czf /tmp/milvus.tar.gz /var/lib/milvus
docker cp milvus-standalone:/tmp/milvus.tar.gz ./milvus_backup_$(date +%Y%m%d).tar.gz
```

---

## 🔒 安全加固

### 防火墙

```bash
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### HTTPS

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## ❓ 常见问题

### Q1: 后端启动失败

```bash
sudo journalctl -u rag-backend -n 100
```

### Q2: 数据库连接失败

```bash
docker compose -f docker-compose-db.yml ps
docker compose -f docker-compose-db.yml logs mysql
```

### Q3: Nginx 502 错误

```bash
sudo systemctl status rag-backend
sudo tail -f /var/log/nginx/error.log
```

---

## 📁 相关文档

- [Docker 镜像优化](./docker-mirrors.md)
- [备份恢复](../operations/backup-restore.md)
- [健康检查](../operations/health-check.md)
