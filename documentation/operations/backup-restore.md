# 备份与恢复

## 📋 备份概述

本文档介绍 RAG 知识问答系统的备份和恢复方案。

---

## 🎯 备份内容

| 内容 | 重要性 | 说明 |
|------|--------|------|
| MySQL 数据库 | ⭐⭐⭐⭐⭐ | 用户、知识库、文档、对话记录 |
| Milvus 向量数据 | ⭐⭐⭐⭐⭐ | 文档向量、检索索引 |
| 上传文件 | ⭐⭐⭐⭐ | 用户上传的原始文档 |
| Redis 缓存 | ⭐⭐ | 验证码、会话缓存（可重建） |
| 配置文件 | ⭐⭐⭐ | .env、docker-compose.yml |

---

## 🚀 自动备份脚本

### 创建备份脚本

```bash
#!/bin/bash
# scripts/backup.sh

set -e

BACKUP_BASE="${1:-./backups}"
BACKUP_DIR="${BACKUP_BASE}/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "=========================================="
echo "RAG 系统备份开始"
echo "备份目录: $BACKUP_DIR"
echo "=========================================="

# 1. 备份 MySQL
echo "[1/3] 备份 MySQL..."
docker exec rag-mysql mysqldump \
    -u root -p"${MYSQL_ROOT_PASSWORD}" \
    --single-transaction \
    rag_db > "$BACKUP_DIR/mysql_rag_db.sql"

# 2. 备份 Milvus
echo "[2/3] 备份 Milvus..."
docker exec milvus-standalone tar -czf /tmp/milvus.tar.gz /var/lib/milvus
docker cp milvus-standalone:/tmp/milvus.tar.gz "$BACKUP_DIR/milvus_data.tar.gz"

# 3. 备份上传文件
echo "[3/3] 备份上传文件..."
tar -czf "$BACKUP_DIR/uploads.tar.gz" ./data/uploads

# 4. 备份配置
cp .env "$BACKUP_DIR/env.backup"
cp docker-compose*.yml "$BACKUP_DIR/"

echo "=========================================="
echo "备份完成!"
echo "备份大小: $(du -sh "$BACKUP_DIR" | cut -f1)"
echo "=========================================="
```

### 设置定时备份

```bash
# 添加执行权限
chmod +x scripts/backup.sh

# 添加到 crontab（每天凌晨 3 点备份）
crontab -e

# 添加以下内容
0 3 * * * /opt/rag-system/scripts/backup.sh /opt/backups >> /var/log/rag-backup.log 2>&1
```

---

## 📦 手动备份

### 备份 MySQL

```bash
# 备份单个数据库
docker exec rag-mysql mysqldump -u root -p rag_db > backup.sql

# 备份所有数据库
docker exec rag-mysql mysqldump -u root -p --all-databases > all_backup.sql

# 压缩备份
docker exec rag-mysql mysqldump -u root -p rag_db | gzip > backup.sql.gz
```

### 备份 Milvus

```bash
# 备份 Milvus 数据
docker exec milvus-standalone tar -czf /tmp/milvus.tar.gz /var/lib/milvus
docker cp milvus-standalone:/tmp/milvus.tar.gz ./milvus_backup.tar.gz
```

### 备份上传文件

```bash
# 备份上传目录
tar -czf uploads_backup.tar.gz ./data/uploads
```

---

## 🔄 恢复步骤

### 恢复 MySQL

```bash
# 方法1：从 SQL 文件恢复
docker exec -i rag-mysql mysql -u root -p rag_db < backup.sql

# 方法2：从压缩文件恢复
gunzip < backup.sql.gz | docker exec -i rag-mysql mysql -u root -p rag_db
```

### 恢复 Milvus

```bash
# 停止 Milvus
docker compose stop milvus

# 恢复数据
docker cp milvus_backup.tar.gz milvus-standalone:/tmp/
docker exec milvus-standalone tar -xzf /tmp/milvus_backup.tar.gz -C /

# 启动 Milvus
docker compose start milvus
```

### 恢复上传文件

```bash
# 恢复上传文件
tar -xzf uploads_backup.tar.gz -C ./
```

---

## 📁 备份目录结构

```
backups/
├── 20240101_030000/
│   ├── mysql_rag_db.sql
│   ├── milvus_data.tar.gz
│   ├── uploads.tar.gz
│   ├── env.backup
│   └── docker-compose.yml
├── 20240102_030000/
│   └── ...
└── 20240103_030000/
    └── ...
```

---

## 🗑️ 备份清理

### 保留策略

```bash
# 保留最近 30 天备份
find /opt/backups -maxdepth 1 -mtime +30 -exec rm -rf {} \;

# 保留最近 10 个备份
ls -dt /opt/backups/*/ | tail -n +11 | xargs rm -rf
```

### 自动清理脚本

```bash
#!/bin/bash
# scripts/cleanup-backups.sh

BACKUP_DIR="/opt/backups"
KEEP_DAYS=30

echo "清理 ${KEEP_DAYS} 天前的备份..."
find "$BACKUP_DIR" -maxdepth 1 -mtime +$KEEP_DAYS -exec rm -rf {} \;
echo "清理完成"
```

---

## 🔍 备份验证

### 定期验证

```bash
#!/bin/bash
# scripts/verify-backup.sh

BACKUP_DIR="$1"

if [ -z "$BACKUP_DIR" ]; then
    echo "用法: $0 <备份目录>"
    exit 1
fi

echo "验证备份: $BACKUP_DIR"

# 检查文件是否存在
for file in mysql_rag_db.sql milvus_data.tar.gz uploads.tar.gz; do
    if [ -f "$BACKUP_DIR/$file" ]; then
        echo "✅ $file 存在 ($(du -sh "$BACKUP_DIR/$file" | cut -f1))"
    else
        echo "❌ $file 不存在"
    fi
done

# 验证 SQL 文件
if [ -f "$BACKUP_DIR/mysql_rag_db.sql" ]; then
    if head -n 5 "$BACKUP_DIR/mysql_rag_db.sql" | grep -q "MySQL dump"; then
        echo "✅ MySQL 备份文件格式正确"
    else
        echo "❌ MySQL 备份文件格式异常"
    fi
fi
```

---

## ⚠️ 注意事项

1. **备份前停止写入**：备份 MySQL 时使用 `--single-transaction` 确保一致性
2. **异地备份**：重要数据建议备份到其他服务器或云存储
3. **定期验证**：定期验证备份文件的完整性和可恢复性
4. **加密敏感数据**：备份文件中的密码等敏感信息应加密存储

---

## ❓ 常见问题

### Q1: 备份文件很大怎么办？

```bash
# 压缩备份
mysqldump ... | gzip > backup.sql.gz

# 分卷压缩
tar -czf - ./data/uploads | split -b 1G - uploads_backup.tar.gz.part
```

### Q2: 恢复失败怎么办？

1. 检查备份文件完整性
2. 检查 MySQL 版本兼容性
3. 检查磁盘空间是否足够
4. 查看详细错误日志

### Q3: 如何备份到远程服务器？

```bash
# 使用 scp
scp -r backups/ user@remote:/backup/

# 使用 rsync
rsync -avz backups/ user@remote:/backup/

# 使用 rclone（支持云存储）
rclone sync backups/ remote:backup/rag-system/
```

---

## 📚 相关文档

- [健康检查](./health-check.md)
- [日志管理](./logging.md)
