# 优化 #11：全局异常处理

## 改动文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/main.py` | 修改 | 添加全局异常处理器 |

## 异常处理策略

| 异常类型 | HTTP 状态码 | 返回内容 | 日志级别 |
|----------|------------|----------|----------|
| `Exception`（通用） | 500 | `{"detail": "服务器内部错误，请稍后重试"}` | ERROR |
| `ValueError` | 400 | `{"detail": "具体错误信息"}` | WARNING |
| `ConnectionError` | 503 | `{"detail": "服务暂时不可用，请稍后重试"}` | ERROR |

## 日志格式

```
ERROR - 未处理异常: GET /api/xxx -> division by zero
Traceback (most recent call last):
  File "...", line ...
    ...
ZeroDivisionError: division by zero
```

## 优势

1. **用户体验**：返回友好错误信息，不暴露代码细节
2. **安全**：生产环境不泄露堆栈信息
3. **可追溯**：日志记录完整堆栈，便于排查
4. **统一格式**：所有错误响应格式一致

## 响应示例

### 服务器内部错误（500）
```json
{
  "detail": "服务器内部错误，请稍后重试",
  "error_type": "ZeroDivisionError"
}
```

### 参数错误（400）
```json
{
  "detail": "用户名不能为空"
}
```

### 服务不可用（503）
```json
{
  "detail": "服务暂时不可用，请稍后重试"
}
```

## 注意事项

1. **HTTPException**：FastAPI 内置的 HTTPException 不会被此处理器捕获，仍按原逻辑处理
2. **error_type 字段**：仅用于调试，生产环境可移除
3. **日志**：所有异常都会记录到日志文件，便于排查
