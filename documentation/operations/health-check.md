# 健康检查

## 📋 概述

本文档介绍 RAG 知识问答系统的健康检查方案。

---

## 🎯 检查内容

| 组件 | 检查项 | 说明 |
|------|--------|------|
| 后端服务 | HTTP 响应 | API 是否正常响应 |
| MySQL | 连接测试 | 数据库是否可连接 |
| Milvus | 连接测试 | 向量库是否可连接 |
| Redis | 连接测试 | 缓存是否可连接 |
| 磁盘空间 | 容量检查 | 是否有足够空间 |
| CPU/内存 | 资源检查 | 资源使用是否正常 |

---

## 🔧 API 健康检查

### 基础健康检查

```http
GET /health
```

**响应：**
```json
{
  "status": "ok"
}
```

### 深度健康检查

```http
GET /health/deep
```

**响应：**
```json
{
  "status": "ok",
  "checks": {
    "mysql": {
      "status": "ok"
    },
    "milvus": {
      "status": "ok"
    },
    "redis": {
      "status": "ok"
    }
  }
}
```

**状态说明：**
- `ok`：正常
- `error`：异常
- `not_configured`：未配置

---

## 🛠️ 健康检查脚本

```bash
#!/bin/bash
# scripts/healthcheck.sh

BACKEND_URL="${1:-http://localhost:8000}"
FRONTEND_URL="${2:-http://localhost:8080}"

echo "=========================================="
echo "RAG 系统健康检查"
echo "=========================================="

CHECKS_PASSED=0
CHECKS_FAILED=0

# 检查函数
check_service() {
    local name=$1
    local url=$2
    
    echo -n "检查 $name ... "
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$url" --connect-timeout 5 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ 正常"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo "❌ 异常 (HTTP $HTTP_CODE)"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
}

# 检查前端
check_service "前端" "$FRONTEND_URL"

# 检查后端
check_service "后端" "$BACKEND_URL/health"

# 检查深度健康
echo ""
echo "【组件检查】"
DEEP_HEALTH=$(curl -s "$BACKEND_URL/health/deep" --connect-timeout 5 2>/dev/null)

for component in mysql milvus redis; do
    echo -n "检查 $component ... "
    STATUS=$(echo "$DEEP_HEALTH" | grep -o "\"$component\":{[^}]*}" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    
    if [ "$STATUS" = "ok" ]; then
        echo "✅ 正常"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    elif [ "$STATUS" = "not_configured" ]; then
        echo "ℹ️  未配置"
    else
        echo "❌ 异常"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
done

# 检查磁盘空间
echo ""
echo "【系统资源】"
echo -n "检查磁盘空间 ... "
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo "✅ 正常 (已使用 ${DISK_USAGE}%)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo "⚠️  警告 (已使用 ${DISK_USAGE}%)"
else
    echo "❌ 危险 (已使用 ${DISK_USAGE}%)"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# 汇总
echo ""
echo "=========================================="
echo "检查结果: 通过 $CHECKS_PASSED, 失败 $CHECKS_FAILED"
if [ "$CHECKS_FAILED" -gt 0 ]; then
    echo "🔴 系统状态: 异常"
    exit 1
else
    echo "🟢 系统状态: 正常"
    exit 0
fi
```

---

## ⏰ 定时健康检查

### 添加到 Crontab

```bash
# 每 5 分钟检查一次
crontab -e

# 添加以下内容
*/5 * * * * /opt/rag-system/scripts/healthcheck.sh >> /var/log/rag-health.log 2>&1
```

### 检查并重启脚本

```bash
#!/bin/bash
# scripts/health-monitor.sh

LOG_FILE="/var/log/rag-health.log"
BACKEND_URL="http://localhost:8000"

# 检查后端
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health" --connect-timeout 5 2>/dev/null || echo "000")

if [ "$HTTP_CODE" != "200" ]; then
    echo "$(date): 后端健康检查失败 (HTTP $HTTP_CODE)，尝试重启..." >> $LOG_FILE
    sudo systemctl restart rag-backend
    sleep 10
    
    # 再次检查
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health" --connect-timeout 5 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" != "200" ]; then
        echo "$(date): 重启后仍然失败" >> $LOG_FILE
    else
        echo "$(date): 重启成功" >> $LOG_FILE
    fi
fi

# 检查磁盘空间
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "$(date): 磁盘空间警告 ($DISK_USAGE%)" >> $LOG_FILE
fi
```

---

## 📊 监控工具集成

### Prometheus + Grafana

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'rag-backend'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:8000']
```

### Zabbix

```bash
# 自定义检查项
UserParameter=rag.health,curl -s http://localhost:8000/health | grep -c "ok"
UserParameter=rag.mysql,docker exec rag-mysql mysqladmin ping 2>/dev/null | grep -c "alive"
```

---

## 📱 告警配置

### 邮件告警

```bash
#!/bin/bash
# scripts/alert-email.sh

SUBJECT="RAG 系统告警: $1"
BODY="$2"
EMAIL="admin@example.com"

echo "$BODY" | mail -s "$SUBJECT" "$EMAIL"
```

### 钉钉/企业微信告警

```bash
#!/bin/bash
# scripts/alert-dingtalk.sh

WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=xxx"
CONTENT="$1"

curl -s -X POST "$WEBHOOK" \
    -H 'Content-Type: application/json' \
    -d "{
        \"msgtype\": \"text\",
        \"text\": {
            \"content\": \"RAG 系统告警: $CONTENT\"
        }
    }"
```

---

## 📋 检查清单

### 日常检查

- [ ] 前端页面可访问
- [ ] 后端 API 正常响应
- [ ] 数据库连接正常
- [ ] 磁盘空间充足
- [ ] 日志无异常错误

### 每周检查

- [ ] 备份文件完整性
- [ ] 系统资源使用趋势
- [ ] 安全日志审查
- [ ] 证书有效期检查

---

## ❓ 常见问题

### Q1: 健康检查失败

```bash
# 手动测试
curl http://localhost:8000/health/deep

# 查看日志
sudo journalctl -u rag-backend -n 100
```

### Q2: 组件状态异常

```bash
# 检查 Docker 容器
docker compose ps

# 检查容器日志
docker compose logs mysql
docker compose logs milvus
```

### Q3: 磁盘空间不足

```bash
# 查看磁盘使用
df -h

# 清理日志
sudo journalctl --vacuum-time=7d

# 清理 Docker
docker system prune -a
```

---

## 📚 相关文档

- [备份恢复](./backup-restore.md)
- [日志管理](./logging.md)
- [性能优化](../optimization/performance.md)
