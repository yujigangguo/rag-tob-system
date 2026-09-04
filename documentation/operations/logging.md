# 日志管理

## 📋 概述

本文档介绍 RAG 知识问答系统的日志配置和管理。

---

## 📁 日志位置

| 日志类型 | 位置 | 说明 |
|----------|------|------|
| 应用日志 | `data/logs/app.log` | 后端应用日志 |
| 访问日志 | `/var/log/rag-backend/access.log` | Nginx 访问日志 |
| 错误日志 | `/var/log/rag-backend/error.log` | Nginx 错误日志 |
| 系统日志 | `journalctl -u rag-backend` | systemd 服务日志 |
| Docker 日志 | `docker compose logs` | 容器日志 |

---

## 🔧 日志配置

### 应用日志配置

**文件**：`app/logging_config.py`

```python
import logging
from logging.handlers import RotatingFileHandler

LOG_DIR = Path(settings.data_dir) / "logs"
LOG_FILE = LOG_DIR / "app.log"

def setup_logging():
    root = logging.getLogger()
    root.setLevel(settings.log_level)
    
    # 控制台输出
    console = logging.StreamHandler()
    root.addHandler(console)
    
    # 文件输出（轮转）
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    root.addHandler(file_handler)
```

### 日志级别

| 级别 | 用途 |
|------|------|
| DEBUG | 调试信息，开发环境使用 |
| INFO | 一般信息，生产环境默认 |
| WARNING | 警告信息 |
| ERROR | 错误信息 |
| CRITICAL | 严重错误 |

**配置方式**：
```bash
# .env 文件
LOG_LEVEL=INFO
```

---

## 📊 日志格式

### 应用日志格式

```
2024-01-01 12:00:00 | INFO    | app.api.chat | 用户登录成功: admin
2024-01-01 12:00:01 | WARNING | app.rag.retrieval | 检索失败 kb=1: timeout
2024-01-01 12:00:02 | ERROR   | app.main | 未处理异常: ...
```

**字段说明**：
- 时间戳
- 日志级别
- 模块名称
- 日志消息

---

## 🔍 日志查看

### 查看应用日志

```bash
# 实时查看
tail -f data/logs/app.log

# 查看最近 100 行
tail -n 100 data/logs/app.log

# 搜索错误
grep "ERROR" data/logs/app.log

# 按时间筛选
grep "2024-01-01" data/logs/app.log
```

### 查看 systemd 日志

```bash
# 查看后端服务日志
sudo journalctl -u rag-backend -f

# 查看最近 100 行
sudo journalctl -u rag-backend -n 100

# 查看今天的日志
sudo journalctl -u rag-backend --since today

# 查看错误日志
sudo journalctl -u rag-backend -p err
```

### 查看 Docker 日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f mysql

# 查看最近 100 行
docker compose logs --tail=100 backend

# 查看特定时间后的日志
docker compose logs --since="2024-01-01T00:00:00" backend
```

---

## 📦 日志轮转

### 应用日志轮转

配置在 `app/logging_config.py` 中：

```python
RotatingFileHandler(
    LOG_FILE,
    maxBytes=10 * 1024 * 1024,  # 单个文件最大 10MB
    backupCount=5,              # 保留 5 个备份
    encoding="utf-8"
)
```

**效果**：
- `app.log` - 当前日志
- `app.log.1` - 第一个备份
- `app.log.2` - 第二个备份
- ...
- `app.log.5` - 最后一个备份

### systemd 日志轮转

```bash
# 配置 journald
sudo vim /etc/systemd/journald.conf

# 添加以下配置
[Journal]
SystemMaxUse=100M
MaxRetentionSec=7day
```

### Docker 日志轮转

```yaml
# docker-compose.yml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 🔎 日志分析

### 统计错误数量

```bash
# 统计今天的错误数
grep "$(date +%Y-%m-%d)" data/logs/app.log | grep -c "ERROR"

# 按小时统计错误
grep "$(date +%Y-%m-%d)" data/logs/app.log | grep "ERROR" | awk '{print substr($2,1,2)}' | sort | uniq -c
```

### 分析访问量

```bash
# 统计 API 访问次数
cat /var/log/rag-backend/access.log | awk '{print $7}' | sort | uniq -c | sort -rn | head -20

# 统计 IP 访问次数
cat /var/log/rag-backend/access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -20
```

### 查找慢请求

```bash
# 查找响应时间超过 1 秒的请求
grep -E "([0-9]+\.[0-9]+s)" /var/log/rag-backend/access.log | awk '{print $NF, $0}' | sort -rn | head -20
```

---

## 🧹 日志清理

### 手动清理

```bash
# 清理 7 天前的日志
find data/logs -name "*.log.*" -mtime +7 -delete

# 清理 systemd 日志
sudo journalctl --vacuum-time=7d

# 清理 Docker 日志
docker system prune
```

### 自动清理脚本

```bash
#!/bin/bash
# scripts/cleanup-logs.sh

# 清理应用日志
find /opt/rag-system/data/logs -name "*.log.*" -mtime +30 -delete

# 清理 systemd 日志
sudo journalctl --vacuum-time=7d

# 清理 Nginx 日志
find /var/log/nginx -name "*.log.*" -mtime +30 -delete

echo "日志清理完成"
```

### 添加到 Crontab

```bash
# 每天凌晨 4 点清理日志
0 4 * * * /opt/rag-system/scripts/cleanup-logs.sh >> /var/log/cleanup.log 2>&1
```

---

## 📱 日志告警

### 错误日志告警

```bash
#!/bin/bash
# scripts/alert-on-error.sh

LOG_FILE="data/logs/app.log"
ERROR_COUNT=$(tail -n 100 "$LOG_FILE" | grep -c "ERROR")

if [ "$ERROR_COUNT" -gt 10 ]; then
    # 发送告警
    curl -s -X POST "https://webhook.example.com" \
        -d "{\"text\": \"RAG 系统错误日志告警: 最近 100 条日志中有 $ERROR_COUNT 条错误\"}"
fi
```

---

## 📋 日志最佳实践

1. **合理设置日志级别**：生产环境使用 INFO 或 WARNING
2. **定期轮转日志**：避免日志文件过大
3. **及时清理旧日志**：释放磁盘空间
4. **监控错误日志**：及时发现问题
5. **保留足够历史**：便于问题排查

---

## ❓ 常见问题

### Q1: 日志文件过大

```bash
# 检查日志大小
du -sh data/logs/*

# 手动轮转
mv data/logs/app.log data/logs/app.log.1
touch data/logs/app.log
```

### Q2: 日志没有输出

```bash
# 检查日志级别配置
grep LOG_LEVEL .env

# 检查日志目录权限
ls -la data/logs/
```

### Q3: 如何查看实时日志

```bash
# 应用日志
tail -f data/logs/app.log

# systemd 日志
sudo journalctl -u rag-backend -f

# Docker 日志
docker compose logs -f backend
```

---

## 📚 相关文档

- [健康检查](./health-check.md)
- [备份恢复](./backup-restore.md)
- [性能优化](../optimization/performance.md)
