# 后端镜像:FastAPI + uv 依赖 + uvicorn
FROM python:3.11-slim

# 安装系统依赖(字体用于验证码,Pillow 需要)
RUN apt-get update && \
    apt-get install -y --no-install-recommends fonts-dejavu-core libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# 配置三镜像源（阿里云、腾讯云、清华）
RUN mkdir -p /etc/pip && \
    echo '[global]\n\
timeout = 60\n\
index-url = https://mirrors.aliyun.com/pypi/simple/\n\
extra-index-url =\n\
    https://mirrors.cloud.tencent.com/pypi/simple/\n\
    https://pypi.tuna.tsinghua.edu.cn/simple/\n\
trusted-host =\n\
    mirrors.aliyuncs.com\
    mirrors.cloud.tencent.com\n\
    pypi.tuna.tsinghua.edu.cn' > /etc/pip.conf && \
    cat /etc/pip.conf

# 安装 uv（使用配置的镜像源）
RUN pip install uv --timeout 120

WORKDIR /app

# 配置 uv 三镜像源
ENV UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV UV_EXTRA_INDEX_URL="https://mirrors.cloud.tencent.com/pypi/simple/|https://pypi.tuna.tsinghua.edu.cn/simple/"
ENV UV_TRUSTED_HOST="mirrors.aliyuncs.com,mirrors.cloud.tencent.com,pypi.tuna.tsinghua.edu.cn"
ENV UV_REQUEST_TIMEOUT=120

# 先复制依赖清单,利用构建缓存
COPY pyproject.toml uv.lock ./

# 方式1: 如果有离线包，使用离线安装
# 方式2: 在线安装（从镜像源下载）
RUN if [ -d "./offline-packages" ]; then \
        echo "使用离线包安装..." && \
        uv pip install --no-cache-dir --find-links ./offline-packages -r pyproject.toml; \
    else \
        echo "从镜像源下载安装..." && \
        uv sync --frozen --no-dev --no-cache; \
    fi

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
