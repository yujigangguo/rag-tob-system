# 优化 #8：数据库连接池调优

## 改动文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/database.py` | 修改 | 优化连接池参数 |

## 连接池参数说明

| 参数 | 值 | 说明 |
|------|-----|------|
| `pool_pre_ping` | `True` | 取连接前自动检测连接是否有效 |
| `pool_recycle` | `3600` | 连接最大存活 1 小时，避免 MySQL 超时断开 |
| `pool_size` | `20` | 常驻连接数，适合中等并发 |
| `max_overflow` | `10` | 高峰期最多可额外创建 10 个连接 |
| `pool_timeout` | `30` | 获取连接最多等待 30 秒 |

## 连接数计算

- **最小连接数**：0（空闲时）
- **常驻连接数**：20
- **最大连接数**：20 + 10 = 30
- **并发能力**：同时处理 30 个请求

## 调优建议

| 场景 | pool_size | max_overflow |
|------|-----------|--------------|
| 开发/测试 | 5 | 5 |
| 小型生产（<100 用户） | 10 | 10 |
| 中型生产（100-1000 用户） | 20 | 10 |
| 大型生产（>1000 用户） | 50 | 20 |

## MySQL 配置匹配

确保 MySQL 的 `max_connections` 大于连接池最大连接数：

```sql
-- 查看当前最大连接数
SHOW VARIABLES LIKE 'max_connections';

-- 设置最大连接数（需要重启 MySQL）
SET GLOBAL max_connections = 200;
```

## 监控连接池状态

```python
# 在代码中获取连接池状态
from app.database import engine

pool = engine.pool
print(f"连接池大小: {pool.size()}")
print(f"当前签出数: {pool.checkedout()}")
print(f"当前空闲数: {pool.checkedin()}")
print(f"当前溢出数: {pool.overflow()}")
```
