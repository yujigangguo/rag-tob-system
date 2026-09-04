# 优化 #20：数据库自动备份

## 改动文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `scripts/backup.sh` | 新增 | 备份脚本 |
| `docker-compose.yml` | 修改 | 添加备份服务 |

## 实现方案

### 1. 创建备份脚本
```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/rag_db_$TIMESTAMP.sql"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
mysqldump -h mysql -u rag_user -prag_pass123 rag_db > $BACKUP_FILE

# 压缩
gzip $BACKUP_FILE

# 删除 7 天前的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "备份完成: $BACKUP_FILE.gz"
```

### 2. 添加备份服务到 docker-compose.yml
```yaml
backup:
  image: mysql:8.0
  container_name: rag-backup
  volumes:
    - ./scripts/backup.sh:/backup.sh
    - ./backups:/backups
  entrypoint: /bin/bash -c
  command: |
    "apt-get update && apt-get install -y cron && 
     echo '0 2 * * * /backup.sh >> /var/log/cron.log 2>&1' > /etc/cron.d/backup &&
     chmod 0644 /etc/cron.d/backup &&
     cron -f"
  depends_on:
    - mysql
  environment:
    MYSQL_PWD: rag_pass123
```

### 3. 手动备份
```bash
# 执行一次性备份
docker exec rag-backup /backup.sh

# 查看备份文件
ls -la backups/
```

## 备份策略

| 项目 | 配置 |
|------|------|
| 备份频率 | 每天凌晨 2 点 |
| 保留天数 | 7 天 |
| 存储位置 | ./backups/ |
| 压缩格式 | gzip |

## 恢复数据

```bash
# 解压备份文件
gunzip backups/rag_db_20240101_020000.sql.gz

# 恢复到数据库
docker exec -i rag-mysql mysql -u rag_user -prag_pass123 rag_db < backups/rag_db_20240101_020000.sql
```

## 注意事项

1. **备份目录**：确保 `./backups/` 目录有足够空间
2. **权限**：备份脚本需要执行权限 `chmod +x scripts/backup.sh`
3. **测试恢复**：定期测试备份文件能否正常恢复
4. **异地备份**：生产环境建议将备份同步到云存储
