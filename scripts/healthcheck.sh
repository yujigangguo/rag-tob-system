#!/bin/bash
# RAG 系统健康检查脚本
# 用法: ./healthcheck.sh [服务地址]

set -e

# 默认服务地址
BACKEND_URL="${1:-http://localhost:8000}"
FRONTEND_URL="${2:-http://localhost:8080}"

echo "=========================================="
echo "RAG 系统健康检查"
echo "后端地址: $BACKEND_URL"
echo "前端地址: $FRONTEND_URL"
echo "=========================================="

# 检查结果
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNED=0

# 检查函数
check_service() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "检查 $name ... "
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$url" --connect-timeout 5 --max-time 10 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "$expected_code" ]; then
        echo "✅ 正常 (HTTP $HTTP_CODE)"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    elif [ "$HTTP_CODE" = "000" ]; then
        echo "❌ 无法连接"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    else
        echo "⚠️  异常 (HTTP $HTTP_CODE)"
        CHECKS_WARNED=$((CHECKS_WARNED + 1))
    fi
}

# 1. 检查前端服务
echo ""
echo "【前端服务】"
check_service "前端首页" "$FRONTEND_URL"

# 2. 检查后端服务
echo ""
echo "【后端服务】"
check_service "后端健康检查" "$BACKEND_URL/health"
check_service "API 文档" "$BACKEND_URL/docs"

# 3. 检查后端深度健康检查
echo ""
echo "【组件检查】"
echo -n "检查 MySQL 连接 ... "
DEEP_HEALTH=$(curl -s "$BACKEND_URL/health/deep" --connect-timeout 5 --max-time 10 2>/dev/null || echo "{}")
MYSQL_STATUS=$(echo "$DEEP_HEALTH" | grep -o '"mysql":{[^}]*}' | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
if [ "$MYSQL_STATUS" = "ok" ]; then
    echo "✅ 正常"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
elif [ -z "$MYSQL_STATUS" ]; then
    echo "❌ 无法获取状态"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
else
    echo "⚠️  异常 ($MYSQL_STATUS)"
    CHECKS_WARNED=$((CHECKS_WARNED + 1))
fi

echo -n "检查 Milvus 连接 ... "
MILVUS_STATUS=$(echo "$DEEP_HEALTH" | grep -o '"milvus":{[^}]*}' | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
if [ "$MILVUS_STATUS" = "ok" ]; then
    echo "✅ 正常"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
elif [ -z "$MILVUS_STATUS" ]; then
    echo "❌ 无法获取状态"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
else
    echo "⚠️  异常 ($MILVUS_STATUS)"
    CHECKS_WARNED=$((CHECKS_WARNED + 1))
fi

echo -n "检查 Redis 连接 ... "
REDIS_STATUS=$(echo "$DEEP_HEALTH" | grep -o '"redis":{[^}]*}' | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
if [ "$REDIS_STATUS" = "ok" ]; then
    echo "✅ 正常"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
elif [ "$REDIS_STATUS" = "not_configured" ]; then
    echo "ℹ️  未配置"
else
    echo "⚠️  异常 ($REDIS_STATUS)"
    CHECKS_WARNED=$((CHECKS_WARNED + 1))
fi

# 4. 检查磁盘空间
echo ""
echo "【系统资源】"
echo -n "检查磁盘空间 ... "
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo "✅ 正常 (已使用 ${DISK_USAGE}%)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo "⚠️  警告 (已使用 ${DISK_USAGE}%)"
    CHECKS_WARNED=$((CHECKS_WARNED + 1))
else
    echo "❌ 危险 (已使用 ${DISK_USAGE}%)"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# 5. 检查 Docker 容器状态
echo ""
echo "【Docker 容器】"
for container in rag-backend rag-frontend rag-mysql milvus-standalone milvus-redis milvus-etcd milvus-minio; do
    echo -n "检查 $container ... "
    STATUS=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "not_found")
    if [ "$STATUS" = "running" ]; then
        echo "✅ 运行中"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    elif [ "$STATUS" = "not_found" ]; then
        echo "ℹ️  不存在"
    else
        echo "❌ 未运行 ($STATUS)"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
done

# 6. 汇总结果
echo ""
echo "=========================================="
echo "检查结果汇总"
echo "=========================================="
echo "✅ 通过: $CHECKS_PASSED"
echo "⚠️  警告: $CHECKS_WARNED"
echo "❌ 失败: $CHECKS_FAILED"
echo ""

if [ "$CHECKS_FAILED" -gt 0 ]; then
    echo "🔴 系统状态: 异常"
    exit 1
elif [ "$CHECKS_WARNED" -gt 0 ]; then
    echo "🟡 系统状态: 警告"
    exit 0
else
    echo "🟢 系统状态: 正常"
    exit 0
fi
