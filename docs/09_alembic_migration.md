# 优化 #9：Alembic 数据库迁移

## 改动文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `pyproject.toml` | 修改 | 添加 `alembic>=1.14.0` 依赖 |
| `alembic.ini` | 新增 | Alembic 配置文件 |
| `alembic/env.py` | 新增 | 环境配置，自动读取数据库连接串 |
| `alembic/script.py.mako` | 新增 | 迁移脚本模板 |
| `alembic/versions/` | 新增 | 迁移脚本存放目录 |
| `scripts/entrypoint.sh` | 新增 | Docker 启动脚本，支持迁移 |
| `Dockerfile` | 修改 | 复制 alembic 目录，使用启动脚本 |
| `docker-compose.yml` | 修改 | 添加 `RUN_MIGRATIONS` 环境变量 |
| `app/main.py` | 修改 | 自动建表改为环境变量控制 |

## 当前状态(2026-09-01)

- ✅ 基线迁移已生成:`alembic/versions/2026_09_01_1418_936b96e574aa_baseline.py`
- ✅ 当前数据库已 `upgrade head` 到 `936b96e574aa`
- ✅ `alembic/env.py` 已加项目根目录路径引导,宿主/容器任意目录均可直接运行
- 以后模型变更流程:改模型 → `uv run alembic revision --autogenerate -m "描述"` → 审查生成的脚本 → `uv run alembic upgrade head`

## 使用方式

### 开发环境（保持原有行为）
```bash
# 默认 AUTO_CREATE_TABLES=true，启动时自动建表
python -m uvicorn app.main:app --reload
```

### 生产环境（使用 Alembic 迁移）

#### 方式一：Docker 部署
```bash
# 设置 RUN_MIGRATIONS=true，启动前自动运行迁移
RUN_MIGRATIONS=true docker compose up -d

# 或在 .env 文件中添加
echo "RUN_MIGRATIONS=true" >> .env
docker compose up -d
```

#### 方式二：手动迁移
```bash
# 生成初始迁移脚本（首次）
alembic revision --autogenerate -m "initial"

# 执行迁移
alembic upgrade head

# 查看当前版本
alembic current

# 查看迁移历史
alembic history
```

### 常用 Alembic 命令
```bash
# 生成新的迁移脚本（自动检测模型变更）
alembic revision --autogenerate -m "描述信息"

# 升级到最新版本
alembic upgrade head

# 升级一个版本
alembic upgrade +1

# 降级一个版本
alembic downgrade -1

# 降级到指定版本
alembic downgrade <revision_id>

# 查看当前数据库版本
alembic current

# 查看所有版本
alembic history --verbose
```

## 工作原理

1. **env.py**：读取 `config.settings.database_url` 作为数据库连接串
2. **自动导入**：`from app import models` 确保所有 ORM 模型被注册到 `Base.metadata`
3. **启动脚本**：`entrypoint.sh` 根据 `RUN_MIGRATIONS` 环境变量决定是否运行迁移
4. **向后兼容**：开发环境默认仍使用 `create_all()` 自动建表

## 注意事项

1. **基线迁移已就绪**:`alembic/versions/` 下已有 baseline 迁移,新环境部署直接 `alembic upgrade head` 即可,无需再生成初始迁移
2. **生产环境**：建议设置 `AUTO_CREATE_TABLES=false`，只使用 Alembic 管理表结构
3. **多实例部署**：确保只有一个实例运行迁移，其他实例等待迁移完成后再启动
4. **备份**：生产环境执行迁移前建议先备份数据库
