# 优化 #6：Redis 缓存

## 改动文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `pyproject.toml` | 修改 | 添加 `redis>=5.0.0` 依赖 |
| `app/redis_client.py` | 新增 | Redis 客户端封装 |
| `app/security.py` | 修改 | 验证码存储改用 Redis |
| `docker-compose.yml` | 修改 | 添加 `REDIS_URL` 环境变量 |

## 功能说明

### 验证码缓存
- **存储位置**：Redis（优先）→ 内存（fallback）
- **过期时间**：5 分钟（可配置）
- **一次性**：验证后自动删除

### 降级策略
1. 配置 `REDIS_URL` → 使用 Redis
2. 未配置或连接失败 → 使用内存存储（重启丢失）

## 配置

### 环境变量
```bash
# 格式: redis://:密码@主机:端口/数据库号
REDIS_URL=redis://:1234@redis:6379/0
```

### docker-compose.yml
```yaml
environment:
  REDIS_URL: redis://:1234@redis:6379/0
```

## 优势

1. **持久化**：容器重启后验证码不丢失
2. **多实例**：多个后端实例共享验证码
3. **自动过期**：Redis 自动清理过期数据
4. **高性能**：内存读写，毫秒级响应

## 扩展用途

Redis 还可用于：
- 会话缓存
- 热点数据缓存
- 分布式锁
- 消息队列
