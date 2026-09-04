# 方案2：生产环境混合部署（推荐）

## 📋 方案概述

在 Linux 服务器上，**应用层原生运行**，**数据库层使用 Docker**，兼顾性能和易维护性。

```
┌─────────────────────────────────────────────────────────────────┐
│                      Linux 服务器 (Ubuntu 22.04)                │
├─────────────────────────────────────────────────────────────────┤
│  Nginx (原生)                                                    │
│  ├── 前端静态文件托管 (http://your-domain.com)                   │
│  ├── 反向代理后端 API (/api → localhost:8000)                    │
│  ├── Gzip 压缩                                                  │
│  ├── 静态资源缓存                                               │
│  └── 请求限流                                                   │
├─────────────────────────────────────────────────────────────────┤
│  Python + Gunicorn (原生)                                        │
│  ├── 4 个 Worker 进程                                           │
│  ├── FastAPI 后端                                               │
│  └── 系统服务管理 (systemd)                                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Docker Compose (仅数据库服务)                              ││
│  │  ┌──────────┐ ┌──────────┐ ┌─────────────────────────────┐ ││
│  │  │  MySQL   │ │  Redis   │ │  Milvus + etcd + MinIO      │ ││
│  │  │  8.0     │ │  7.x     │ │  v2.4.4                     │ ││
│  │  │  :3306   │ │  :6379   │ │  :19530                     │ ││
│  │  └──────────┘ └──────────┘ └─────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ 优点

| 优点 | 说明 |
|------|------|
| 🚀 **应用性能最优** | Python/Nginx 原生运行，无虚拟化开销 |
| 🔍 **调试方便** | 日志、进程、性能监控直接查看 |
| 📦 **数据库隔离** | Docker 管理，升级备份简单 |
| 🔧 **精细调优** | 可针对 Nginx、Python、MySQL 单独优化 |
| 💾 **资源利用率高** | 无 Docker 额外开销 |

---

## 📋 前置条件

| 软件 | 版本 | 安装命令 |
|------|------|----------|
| Ubuntu | 22.04 LTS | - |
| Python | 3.11+ | `sudo apt install python3.11` |
| Node.js | 18+ | `curl -fsSL https://deb.nodesource.com/setup_18.x \| sudo -E bash -` |
| Docker | 最新 | `curl -fsSL https://get.docker.com \| sh` |
| Docker Compose | 最新 | `sudo apt install docker-compose-plugin` |
| Nginx | 最新 | `sudo apt install nginx` |

---

## 🚀 完整部署步骤

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

# 安装 Docker Compose
sudo apt install -y docker-compose-plugin

# 安装 Nginx
sudo apt install -y nginx

# 重新登录以使 Docker 组生效
logout
```

### 第二步：克隆项目

```bash
# 克隆代码
cd /opt
sudo mkdir rag-system
sudo chown $USER:$USER rag-system
cd rag-system
git clone <你的仓库地址> .
```

### 第三步：启动数据库服务

```bash
# 创建数据目录
mkdir -p volumes/{etcd,minio,milvus,redis,mysql}

# 创建 docker-compose-db.yml（仅数据库服务）
cat > docker-compose-db.yml << 'EOF'
version: '3.8'

services:
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
      - "9091:9091"
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
      - --max-connections=200
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 12
EOF

# 启动数据库服务
docker compose -f docker-compose-db.yml up -d

# 检查状态
docker compose -f docker-compose-db.yml ps
```

### 第四步：配置环境变量

```bash
# 创建生产环境配置
cat > .env << 'EOF'
# ===== 应用配置 =====
SECRET_KEY=$(openssl rand -hex 32)
ACCESS_TOKEN_EXPIRE_MINUTES=1440
LOG_LEVEL=INFO

# ===== MySQL =====
DB_HOST=localhost
DB_PORT=3306
DB_USER=rag_user
DB_PASSWORD=rag_pass123
DB_NAME=rag_db

# ===== Redis =====
REDIS_URL=redis://:1234@localhost:6379/0

# ===== Milvus =====
MILVUS_URI=http://localhost:19530

# ===== 大模型 =====
LLM_API_KEY=你的API密钥
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-max

# ===== Embedding =====
EMBEDDING_API_KEY=你的API密钥
EMBEDDING_MODEL=text-embedding-v3
EMBEDDING_DIM=1024

# ===== 数据库迁移 =====
RUN_MIGRATIONS=true
AUTO_CREATE_TABLES=false
EOF

# 生成随机密钥并替换
sed -i "s/\$(openssl rand -hex 32)/$(openssl rand -hex 32)/" .env
```

### 第五步：安装 Python 依赖

```bash
# 安装 uv
pip install uv

# 创建虚拟环境并安装依赖
uv sync

# 运行数据库迁移
uv run alembic upgrade head
```

### 第六步：构建前端

```bash
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 复制到 Nginx 目录
sudo mkdir -p /var/www/rag-frontend
sudo cp -r dist/* /var/www/rag-frontend/
sudo chown -R www-data:www-data /var/www/rag-frontend

cd ..
```

### 第七步：配置 Nginx

```bash
# 创建 Nginx 配置
sudo cat > /etc/nginx/sites-available/rag-system << 'EOF'
# 请求限流配置
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;

server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或 IP

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript;

    # 前端静态文件
    root /var/www/rag-frontend;
    index index.html;

    # 前端路由 (history 模式)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # API 反向代理
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 流式支持
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
    }

    # 安全响应头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 上传文件大小限制
    client_max_body_size 10m;
}
EOF

# 启用配置
sudo ln -sf /etc/nginx/sites-available/rag-system /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 第八步：配置 systemd 服务

```bash
# 创建后端服务文件
sudo cat > /etc/systemd/system/rag-backend.service << 'EOF'
[Unit]
Description=RAG System Backend
After=network.target docker.service
Requires=docker.service

[Service]
Type=exec
User=root
WorkingDirectory=/opt/rag-system
Environment="PATH=/opt/rag-system/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/rag-system/.venv/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 300 \
    --keep-alive 5 \
    --access-logfile /var/log/rag-backend/access.log \
    --error-logfile /var/log/rag-backend/error.log
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 创建日志目录
sudo mkdir -p /var/log/rag-backend

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable rag-backend
sudo systemctl start rag-backend

# 检查状态
sudo systemctl status rag-backend
```

### 第九步：验证部署

```bash
# 检查数据库服务
docker compose -f docker-compose-db.yml ps

# 检查后端服务
sudo systemctl status rag-backend

# 检查 Nginx
sudo systemctl status nginx

# 测试 API
curl http://localhost/health
curl http://localhost/health/deep

# 查看日志
sudo journalctl -u rag-backend -f
sudo tail -f /var/log/rag-backend/access.log
```

---

## 🔧 日常运维命令

### 服务管理

```bash
# 后端服务
sudo systemctl start rag-backend    # 启动
sudo systemctl stop rag-backend     # 停止
sudo systemctl restart rag-backend  # 重启
sudo systemctl status rag-backend   # 状态
sudo journalctl -u rag-backend -f   # 查看日志

# Nginx
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx
sudo nginx -t                        # 测试配置

# 数据库服务
docker compose -f docker-compose-db.yml up -d      # 启动
docker compose -f docker-compose-db.yml down        # 停止
docker compose -f docker-compose-db.yml restart     # 重启
docker compose -f docker-compose-db.yml logs -f     # 查看日志
```

### 代码更新

```bash
cd /opt/rag-system

# 拉取最新代码
git pull

# 更新后端依赖
uv sync

# 运行数据库迁移（如有）
uv run alembic upgrade head

# 重启后端
sudo systemctl restart rag-backend

# 重新构建前端
cd frontend
npm install
npm run build
sudo cp -r dist/* /var/www/rag-frontend/
cd ..
```

### 数据备份

```bash
# 创建备份目录
mkdir -p /opt/rag-system/backups/$(date +%Y%m%d)

# 备份 MySQL
docker exec rag-mysql mysqldump -u root -p${MYSQL_ROOT_PASSWORD} rag_db \
    > /opt/rag-system/backups/$(date +%Y%m%d)/mysql_rag_db.sql

# 备份 Milvus 数据
docker exec milvus-standalone tar -czf /tmp/milvus.tar.gz /var/lib/milvus
docker cp milvus-standalone:/tmp/milvus.tar.gz \
    /opt/rag-system/backups/$(date +%Y%m%d)/milvus_data.tar.gz

# 备份上传文件
tar -czf /opt/rag-system/backups/$(date +%Y%m%d)/uploads.tar.gz \
    /opt/rag-system/data/uploads

# 保留最近 30 天备份
find /opt/rag-system/backups -maxdepth 1 -mtime +30 -exec rm -rf {} \;
```

---

## 🔒 安全加固

### 1. 配置防火墙

```bash
# 安装 UFW
sudo apt install ufw

# 配置规则
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable
sudo ufw status
```

### 2. 配置 HTTPS（Let's Encrypt）

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 3. 修改默认密码

```bash
# 编辑 .env 文件
vim /opt/rag-system/.env

# 修改以下配置
SECRET_KEY=你的随机密钥
MYSQL_ROOT_PASSWORD=强密码
MYSQL_PASSWORD=强密码
DB_PASSWORD=强密码
```

---

## 📊 监控

### 健康检查脚本

```bash
# 创建定时健康检查
cat > /opt/rag-system/scripts/health-monitor.sh << 'EOF'
#!/bin/bash
LOG_FILE="/var/log/rag-backend/health.log"

# 检查后端
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health)
if [ "$HTTP_CODE" != "200" ]; then
    echo "$(date): Backend health check failed (HTTP $HTTP_CODE)" >> $LOG_FILE
    sudo systemctl restart rag-backend
fi

# 检查磁盘空间
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "$(date): Disk usage critical ($DISK_USAGE%)" >> $LOG_FILE
fi
EOF

chmod +x /opt/rag-system/scripts/health-monitor.sh

# 添加到 crontab（每 5 分钟检查一次）
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/rag-system/scripts/health-monitor.sh") | crontab -
```

---

## 📁 文件结构

```
/opt/rag-system/
├── app/                          # 后端代码
├── config/                       # 配置文件
├── frontend/                     # 前端代码
├── data/                         # 数据目录
│   ├── uploads/                  # 上传文件
│   └── logs/                     # 应用日志
├── volumes/                      # Docker 数据卷
│   ├── etcd/
│   ├── minio/
│   ├── milvus/
│   ├── redis/
│   └── mysql/
├── backups/                      # 备份文件
├── scripts/                      # 脚本
├── .env                          # 环境变量
├── docker-compose-db.yml         # 数据库服务配置
└── pyproject.toml                # Python 依赖

/etc/nginx/sites-available/rag-system  # Nginx 配置
/etc/systemd/system/rag-backend.service # 后端服务配置
/var/www/rag-frontend/                  # 前端静态文件
/var/log/rag-backend/                   # 后端日志
```

---

## ❓ 常见问题

### Q1: 后端启动失败

```bash
# 查看详细错误
sudo journalctl -u rag-backend -n 100

# 检查端口占用
sudo netstat -tlnp | grep 8000

# 手动启动测试
cd /opt/rag-system
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Q2: 数据库连接失败

```bash
# 检查 Docker 容器状态
docker compose -f docker-compose-db.yml ps

# 检查 MySQL 日志
docker compose -f docker-compose-db.yml logs mysql

# 测试连接
docker exec -it rag-mysql mysql -u rag_user -p rag_db
```

### Q3: Nginx 502 错误

```bash
# 检查后端是否运行
sudo systemctl status rag-backend

# 检查后端日志
sudo journalctl -u rag-backend -n 50

# 检查 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log
```
