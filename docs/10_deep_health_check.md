# 优化 #10：深度健康检查

## 改动文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/main.py` | 修改 | 添加 `/health/deep` 接口 |

## 新增接口

### `GET /health/deep`

深度健康检查，验证各组件连接状态。

**响应示例（正常）：**
```json
{
  "status": "ok",
  "checks": {
    "mysql": {"status": "ok"},
    "milvus": {"status": "ok"},
    "redis": {"status": "not_configured"}
  }
}
```

**响应示例（异常）：**
```json
{
  "status": "degraded",
  "checks": {
    "mysql": {"status": "ok"},
    "milvus": {"status": "error", "detail": "Connection refused"},
    "redis": {"status": "not_configured"}
  }
}
```

## 检查项目

| 组件 | 检查方式 | 状态值 |
|------|----------|--------|
| MySQL | `SELECT 1` | ok / error |
| Milvus | `list_collections()` | ok / error |
| Redis | `PING` | ok / error / not_configured |

## 使用场景

1. **Docker 健康检查**：可配置为容器健康检查端点
2. **负载均衡器**：判断实例是否可用
3. **监控系统**：定期检测各组件状态
4. **故障排查**：快速定位哪个组件异常

## Docker 健康检查配置（可选）

```yaml
# docker-compose.yml
backend:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health/deep"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```
