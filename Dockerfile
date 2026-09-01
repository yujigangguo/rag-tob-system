# 后端镜像:FastAPI + uv 依赖 + uvicorn
FROM python:3.11-slim

# 安装系统依赖(字体用于验证码,Pillow 需要)
RUN apt-get update && \
    apt-get install -y --no-install-recommends fonts-dejavu-core libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 先复制依赖清单,利用构建缓存
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

# 复制应用代码与数据目录
COPY app/ app/
COPY config/ config/
COPY data/ data/

EXPOSE 8000

# 启动时自动建表并运行服务
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
