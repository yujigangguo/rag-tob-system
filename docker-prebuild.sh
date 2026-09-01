#!/bin/bash
# 预下载 Python 依赖包（在宿主机执行）
# 解决 Docker 构建时网络超时问题

set -e

echo "=== 预下载 Python 依赖包 ==="

# 创建离线包目录
mkdir -p ./offline-packages

# 使用 uv 导出依赖并下载
echo "下载依赖包到 ./offline-packages ..."
uv pip download \
    -r pyproject.toml \
    --python-version 3.11 \
    -d ./offline-packages \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyuncs.com

echo "=== 下载完成 ==="
echo "离线包位置: ./offline-packages"
echo "现在可以运行: docker compose up -d --build"
