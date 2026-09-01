#!/bin/bash
set -e

# 数据库迁移(如果设置了 RUN_MIGRATIONS=true)
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    uv run alembic upgrade head
    echo "Migrations completed."
fi

# 启动应用
echo "Starting application..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
