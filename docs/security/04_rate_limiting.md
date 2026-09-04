# 优化 #4：接口限频

## 改动文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `pyproject.toml` | 修改 | 添加 `slowapi>=0.1.9` 依赖 |
| `app/main.py` | 修改 | 添加限频中间件 |
| `app/api/auth.py` | 修改 | 登录/注册接口添加限频 |

## 限频策略

| 接口 | 限制 | 说明 |
|------|------|------|
| `POST /auth/register` | 3次/分钟 | 防止恶意注册 |
| `POST /auth/login` | 5次/分钟 | 防止暴力破解 |
| 其他接口 | 默认不限制 | 可按需添加 |

## 工作原理

1. **IP 识别**：按客户端 IP 地址统计请求次数
2. **滑动窗口**：使用滑动窗口算法，精确统计
3. **自动清理**：过期的记录自动清理，不占用内存

## 错误响应

当超过限频时，返回 `429 Too Many Requests`：

```json
{
  "detail": "Rate limit exceeded: 5 per 1 minute"
}
```

## 配置说明

### 修改限频规则
在接口装饰器中修改：
```python
@limiter.limit("10/minute")  # 每分钟10次
@limiter.limit("100/hour")   # 每小时100次
@limiter.limit("1000/day")   # 每天1000次
```

### 支持的时间单位
- `second`：秒
- `minute`：分钟
- `hour`：小时
- `day`：天

## 使用场景

1. **防暴力破解**：限制登录尝试次数
2. **防恶意注册**：限制注册频率
3. **防 DDoS**：限制 API 调用频率
4. **资源保护**：防止滥用计算资源

## 注意事项

1. **反向代理**：如果使用 Nginx，需要配置 `X-Forwarded-For` 头
2. **共享 IP**：公司内网可能共享 IP，会影响所有用户
3. **白名单**：可添加白名单排除特定 IP
4. **分布式**：多实例部署需要使用 Redis 存储限频数据

## 扩展：为其他接口添加限频

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/some-endpoint")
@limiter.limit("60/minute")
def some_endpoint(request: Request):
    return {"message": "ok"}
```
