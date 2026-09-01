# 后端镜像:FastAPI + uv 依赖 + uvicorn
FROM python:3.11-slim

# 安装系统依赖(字体用于验证码,Pillow 需要)
RUN apt-get update && \
    apt-get install -y --no-install-recommends fonts-dejavu-core libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# 安装 uv (使用国内镜像)
RUN pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app

# 配置 uv 镜像源(国内加速)
ENV UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV UV_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# 先复制依赖清单,利用构建缓存
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

# 复制应用代码与数据目录
COPY app/ app/
COPY config/ config/
COPY data/ data/
COPY alembic/ alembic/
COPY alembic.ini ./
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

# 启动入口(支持数据库迁移)
ENTRYPOINT ["/entrypoint.sh"]
