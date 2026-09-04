#!/bin/bash
# RAG 系统备份脚本
# 用法: ./backup.sh [备份目录]

set -e

# 默认备份目录
BACKUP_BASE="${1:-./backups}"
BACKUP_DIR="${BACKUP_BASE}/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "=========================================="
echo "RAG 系统备份开始"
echo "备份目录: $BACKUP_DIR"
echo "=========================================="

# 1. 备份 MySQL 数据库
echo ""
echo "[1/3] 备份 MySQL 数据库..."
if docker ps | grep -q rag-mysql; then
    docker exec rag-mysql mysqldump \
        -u root \
        -p"${MYSQL_ROOT_PASSWORD:-root123456}" \
        --single-transaction \
        --routines \
        --triggers \
        rag_db > "$BACKUP_DIR/mysql_rag_db.sql" 2>/dev/null || {
            echo "警告: MySQL 备份失败，可能是密码错误或数据库不存在"
            echo "尝试使用环境变量中的密码..."
            docker exec rag-mysql mysqldump \
                -u "${DB_USER:-rag_user}" \
                -p"${DB_PASSWORD:-rag_pass123}" \
                --single-transaction \
                rag_db > "$BACKUP_DIR/mysql_rag_db.sql" 2>/dev/null || echo "MySQL 备份失败"
        }
    echo "MySQL 备份完成: mysql_rag_db.sql"
else
    echo "警告: MySQL 容器未运行，跳过备份"
fi

# 2. 备份 Milvus 数据
echo ""
echo "[2/3] 备份 Milvus 数据..."
if docker ps | grep -q milvus-standalone; then
    # 创建 Milvus 快照目录
    docker exec milvus-standalone mkdir -p /tmp/backup 2>/dev/null || true
    
    # 复制 Milvus 数据
    MILVUS_VOLUME="${MILVUS_VOLUME_DIR:-./volumes}/milvus"
    if [ -d "$MILVUS_VOLUME" ]; then
        tar -czf "$BACKUP_DIR/milvus_data.tar.gz" -C "$(dirname "$MILVUS_VOLUME")" "$(basename "$MILVUS_VOLUME")" 2>/dev/null || echo "Milvus 数据备份失败"
        echo "Milvus 备份完成: milvus_data.tar.gz"
    else
        echo "警告: Milvus 数据目录不存在: $MILVUS_VOLUME"
    fi
else
    echo "警告: Milvus 容器未运行，跳过备份"
fi

# 3. 备份上传文件
echo ""
echo "[3/3] 备份上传文件..."
UPLOAD_DIR="./data/uploads"
if [ -d "$UPLOAD_DIR" ]; then
    tar -czf "$BACKUP_DIR/uploads.tar.gz" -C "./data" "uploads" 2>/dev/null || echo "上传文件备份失败"
    echo "上传文件备份完成: uploads.tar.gz"
else
    echo "警告: 上传文件目录不存在: $UPLOAD_DIR"
fi

# 4. 备份配置文件
echo ""
echo "[额外] 备份配置文件..."
cp .env "$BACKUP_DIR/env.backup" 2>/dev/null || echo "警告: .env 文件不存在"
cp docker-compose.yml "$BACKUP_DIR/docker-compose.yml.backup" 2>/dev/null || echo "警告: docker-compose.yml 不存在"

# 5. 创建备份信息文件
cat > "$BACKUP_DIR/backup_info.txt" << EOF
备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份目录: $BACKUP_DIR
备份内容:
- MySQL 数据库: mysql_rag_db.sql
- Milvus 数据: milvus_data.tar.gz
- 上传文件: uploads.tar.gz
- 配置文件: env.backup, docker-compose.yml.backup

恢复方法:
1. 恢复 MySQL: docker exec -i rag-mysql mysql -u root -p rag_db < mysql_rag_db.sql
2. 恢复 Milvus: tar -xzf milvus_data.tar.gz -C /目标目录
3. 恢复上传文件: tar -xzf uploads.tar.gz -C ./data
EOF

# 6. 计算备份大小
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

echo ""
echo "=========================================="
echo "备份完成!"
echo "备份目录: $BACKUP_DIR"
echo "备份大小: $BACKUP_SIZE"
echo "=========================================="
echo ""
echo "备份文件列表:"
ls -lh "$BACKUP_DIR"
