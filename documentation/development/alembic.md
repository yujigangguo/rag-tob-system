# Alembic 数据库迁移

## 📋 概述

Alembic 是 SQLAlchemy 的数据库迁移工具，用于管理数据库表结构的变更。

---

## 🚀 常用命令

### 创建迁移

```bash
# 自动生成迁移脚本
uv run alembic revision --autogenerate -m "描述变更内容"

# 手动创建空迁移
uv run alembic revision -m "描述变更内容"
```

### 执行迁移

```bash
# 升级到最新版本
uv run alembic upgrade head

# 升级一个版本
uv run alembic upgrade +1

# 降级一个版本
uv run alembic downgrade -1

# 降级到指定版本
uv run alembic downgrade <revision_id>
```

### 查看状态

```bash
# 查看当前版本
uv run alembic current

# 查看历史
uv run alembic history

# 查看迁移脚本
uv run alembic show head
```

---

## 📝 迁移脚本示例

```python
"""add user avatar field

Revision ID: abc123
Revises: def456
Create Date: 2024-01-01 12:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123'
down_revision = 'def456'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('users', sa.Column('avatar_url', sa.String(500), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'avatar_url')
```

---

## ⚠️ 注意事项

1. **备份数据库**后再执行迁移
2. 检查自动生成的迁移脚本是否正确
3. 测试环境先验证，再在生产环境执行

---

## 📚 相关文档

- [数据库设计](../technical/database.md)
- [开发指南](./setup.md)
