#!/bin/bash
set -e

# 等待依赖服务就绪
echo "Waiting for MySQL to be ready..."
while ! nc -z ${DB_HOST:-mysql} ${DB_PORT:-3306} 2>/dev/null; do
    sleep 1
done
echo "MySQL is ready."

# 数据库迁移(如果设置了 RUN_MIGRATIONS=true)
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    uv run alembic upgrade head
    echo "Migrations completed."
fi

# 启动应用（使用 Gunicorn 多 Worker 模式）
echo "Starting application with Gunicorn..."
exec uv run gunicorn app.main:app \
    --workers ${GUNICORN_WORKERS:-4} \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 300 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile -
