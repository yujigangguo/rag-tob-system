#!/bin/bash
echo "=== 检查镜像源可用性 ==="
echo ""

# Python 镜像源（阿里云、腾讯云、清华）
echo "📦 Python 镜像源:"
echo "-------------------"
python_mirrors=(
    "阿里云|https://mirrors.aliyun.com/pypi/simple/"
    "腾讯云|https://mirrors.cloud.tencent.com/pypi/simple/"
    "清华大学|https://pypi.tuna.tsinghua.edu.cn/simple/"
)

for item in "${python_mirrors[@]}"; do
    IFS='|' read -r name url <<< "$item"
    printf "%-12s %-55s " "$name" "$url"
    if curl -s --connect-timeout 5 --max-time 10 "$url" > /dev/null 2>&1; then
        echo "✅ 可用"
    else
        echo "❌ 不可用"
    fi
done

echo ""

# npm 镜像源
echo "📦 npm 镜像源:"
echo "-------------------"
npm_mirrors=(
    "淘宝 npm|https://registry.npmmirror.com"
)

for item in "${npm_mirrors[@]}"; do
    IFS='|' read -r name url <<< "$item"
    printf "%-12s %-55s " "$name" "$url"
    if curl -s --connect-timeout 5 --max-time 10 "$url" > /dev/null 2>&1; then
        echo "✅ 可用"
    else
        echo "❌ 不可用"
    fi
done

echo ""
echo "=== 检查完成 ==="
