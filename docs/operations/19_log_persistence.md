# 优化 #19：日志持久化

## 改动文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/logging_config.py` | 修改 | 添加文件日志处理器 |
| `docker-compose.yml` | 修改 | 挂载日志目录 |

## 实现方案

### 1. 更新 logging_config.py
```python
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    log_dir = os.getenv("LOG_DIR", "/app/logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # 文件处理器：10MB 轮转，保留 5 个备份
    file_handler = RotatingFileHandler(
        f"{log_dir}/app.log",
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    ))
    
    # 添加到根日志器
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
```

### 2. 更新 docker-compose.yml
```yaml
backend:
  volumes:
    - ./data:/app/data
    - ./logs:/app/logs  # 新增：日志持久化
```

### 3. 日志轮转策略
| 参数 | 值 | 说明 |
|------|-----|------|
| maxBytes | 10MB | 单个日志文件最大大小 |
| backupCount | 5 | 保留 5 个备份文件 |

## 日志文件结构
```
logs/
├── app.log          # 当前日志
├── app.log.1        # 轮转备份 1
├── app.log.2        # 轮转备份 2
├── app.log.3        # 轮转备份 3
├── app.log.4        # 轮转备份 4
└── app.log.5        # 轮转备份 5
```

## 查看日志
```bash
# 实时查看日志
tail -f logs/app.log

# 查看错误日志
grep "ERROR" logs/app.log

# Docker 日志
docker logs -f rag-backend
```
