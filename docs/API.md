# RAG System 接口文档

基于 FastAPI 的 RAG(检索增强生成)问答服务接口说明。

## 1. 服务信息

| 项 | 值 |
|----|-----|
| 服务框架 | FastAPI |
| 默认地址 | `http://127.0.0.1:8000` |
| 协议 | HTTP + JSON(UTF-8) |
| 启动命令 | `uv run uvicorn app.api:app --host 0.0.0.0 --port 8000` |

> 启动时(lifespan)会自动加载 Milvus 向量库与 BM25 索引;
> 请确保已先执行 `uv run python scripts/ingest.py` 完成建库,否则 `/ask` 无数据可查。

## 2. 在线交互式文档

FastAPI 自动生成,无需额外编写:

- Swagger UI:`http://127.0.0.1:8000/docs` —— 可视化,可在线发请求调试
- ReDoc:`http://127.0.0.1:8000/redoc` —— 只读文档

---

## 3. 接口列表

### 3.1 健康检查

**`GET /health`**

用于存活探测 / 负载均衡探活。

**响应示例:**

```json
{ "status": "ok" }
```

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 固定返回 `ok` |

---

### 3.2 问答

**`POST /ask`**

提交问题,返回基于知识库生成的回答及引用来源。

**请求体(JSON):**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | string | 是 | 用户问题 |

```json
{ "question": "年假有几天?" }
```

**响应(JSON):**

| 字段 | 类型 | 说明 |
|------|------|------|
| answer | string | 生成的回答,带 `[来源: xxx]` 标注 |
| sources | string[] | 本次回答引用的文档路径(重排后 top-k) |

```json
{
  "answer": "根据星云科技员工手册,年假天数按工作年限划分 [来源: 员工手册.md]:\n- 工作满 1 年不满 3 年:每年 5 天\n- 工作满 3 年不满 5 年:每年 10 天\n- 工作满 5 年及以上:每年 15 天",
  "sources": [
    "E:\\deepseek\\RAG\\data\\raw\\员工手册.md"
  ]
}
```

**状态码:**

| 状态码 | 场景 |
|--------|------|
| 200 | 成功(无论是否命中,均返回 `answer`) |
| 422 | 请求体格式错误(如缺 `question` 字段) |
| 500 | 服务内部错误(如 LLM / 向量库调用失败) |

> 未命中知识库时,`answer` 会返回「根据已有资料,无法回答该问题」,状态码仍为 200。

---

## 4. 调用示例

### 4.1 curl

```bash
# Windows PowerShell 建议用 curl.exe(正确处理 UTF-8)
curl.exe -X POST http://127.0.0.1:8000/ask ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"年假有几天?\"}"
```

```bash
# macOS / Linux
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"年假有几天?"}'
```

### 4.2 Python(httpx,推荐,无编码问题)

```python
import httpx

# 健康检查
print(httpx.get("http://127.0.0.1:8000/health").json())

# 问答
r = httpx.post(
    "http://127.0.0.1:8000/ask",
    json={"question": "智能音箱多少钱?"},
    timeout=60,
)
data = r.json()
print("回答:", data["answer"])
print("来源:", data["sources"])
```

### 4.3 Python(requests)

```python
import requests

r = requests.post(
    "http://127.0.0.1:8000/ask",
    json={"question": "加班费怎么算?"},
    timeout=60,
)
print(r.json())
```

### 4.4 JavaScript(fetch)

```javascript
const r = await fetch("http://127.0.0.1:8000/ask", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ question: "年假有几天?" }),
});
const data = await r.json();
console.log(data.answer);
```

---

## 5. 注意事项

1. **编码**:请求与响应均为 UTF-8。Windows PowerShell 5.1 的 `Invoke-RestMethod` 对中文有 GBK 编码坑,建议用 `curl.exe`、Python `httpx` 或浏览器 `/docs`。
2. **首问延迟**:首次提问若向量库未加载可能稍慢;服务启动已预热,一般无感。
3. **重排序**:未配置 `RERANK_API_KEY` 时自动跳过精排,`sources` 为混合检索(向量 + BM25)融合后的前 `FINAL_TOP_K` 条。
4. **配置项**:模型、检索条数等见 `.env`(或 `config/settings.py`),改后需重启服务。
