# 优化清单

## 📋 上线前检查清单

在将 RAG 系统部署到生产环境之前，请完成以下检查项。

---

## 🔒 安全检查

- [ ] 修改默认密码（管理员账号）
- [ ] 修改 `SECRET_KEY` 为随机字符串
- [ ] 修改 MySQL root 密码
- [ ] 修改 Redis 密码
- [ ] 配置 CORS 允许的域名
- [ ] 配置防火墙规则
- [ ] 启用 HTTPS
- [ ] 配置请求限流

---

## ⚙️ 配置检查

- [ ] 配置正确的 API 密钥
- [ ] 配置正确的数据库连接
- [ ] 配置正确的 Redis 连接
- [ ] 配置正确的 Milvus 连接
- [ ] 设置合适的日志级别
- [ ] 配置数据目录权限

---

## 🚀 性能检查

- [ ] 启用 Gunicorn 多 Worker
- [ ] 配置 Nginx Gzip 压缩
- [ ] 配置静态资源缓存
- [ ] 配置数据库连接池
- [ ] 启用 Embedding 缓存
- [ ] 配置 Docker 资源限制

---

## 💾 备份检查

- [ ] 配置 MySQL 定时备份
- [ ] 配置 Milvus 数据备份
- [ ] 配置上传文件备份
- [ ] 测试备份恢复流程
- [ ] 配置备份保留策略

---

## 📊 监控检查

- [ ] 配置健康检查
- [ ] 配置日志轮转
- [ ] 配置告警通知
- [ ] 测试告警是否生效
- [ ] 配置监控面板（可选）

---

## 🧪 功能测试

- [ ] 测试用户登录
- [ ] 测试知识库创建
- [ ] 测试文档上传
- [ ] 测试智能问答
- [ ] 测试对话导出
- [ ] 测试文档预览
- [ ] 测试批量操作

---

## 📝 文档检查

- [ ] 记录服务器信息
- [ ] 记录数据库信息
- [ ] 记录 API 密钥位置
- [ ] 记录备份策略
- [ ] 记录运维流程

---

## 🔧 配置模板

### 生产环境 .env 模板

```bash
# ===== 应用配置 =====
SECRET_KEY=生成随机密钥
ACCESS_TOKEN_EXPIRE_MINUTES=1440
LOG_LEVEL=WARNING
AUTO_CREATE_TABLES=false

# ===== MySQL =====
DB_HOST=localhost
DB_PORT=3306
DB_USER=rag_user
DB_PASSWORD=强密码
DB_NAME=rag_db

# ===== Redis =====
REDIS_URL=redis://:强密码@localhost:6379/0

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
```

---

## ✅ 检查脚本

```bash
#!/bin/bash
# scripts/pre-deploy-check.sh

echo "=========================================="
echo "RAG 系统上线前检查"
echo "=========================================="

ERRORS=0

# 检查 SECRET_KEY
if grep -q "change-me-in-production-please" .env; then
    echo "❌ SECRET_KEY 使用默认值"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ SECRET_KEY 已配置"
fi

# 检查 API 密钥
if grep -q "LLM_API_KEY=$" .env || grep -q "LLM_API_KEY=你的" .env; then
    echo "❌ LLM_API_KEY 未配置"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ LLM_API_KEY 已配置"
fi

# 检查数据库密码
if grep -q "DB_PASSWORD=rag_pass123" .env; then
    echo "⚠️  DB_PASSWORD 使用默认密码"
fi

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Docker 已安装"
fi

# 检查磁盘空间
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "⚠️  磁盘空间不足 ($DISK_USAGE%)"
else
    echo "✅ 磁盘空间充足 ($DISK_USAGE%)"
fi

echo ""
echo "=========================================="
if [ "$ERRORS" -gt 0 ]; then
    echo "❌ 发现 $ERRORS 个问题，请修复后再部署"
    exit 1
else
    echo "✅ 检查通过，可以部署"
    exit 0
fi
```

---

## 📚 相关文档

- [部署方案](../deployment/README.md)
- [性能优化](./performance.md)
- [备份恢复](../operations/backup-restore.md)
