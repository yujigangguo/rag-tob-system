# 文档迁移说明

## 📋 概述

本文档说明旧文档 (`docs/`) 到新文档 (`documentation/`) 的迁移对应关系。

---

## 📁 文档映射表

### 旧文档 → 新文档

| 旧文档 | 新文档 | 说明 |
|--------|--------|------|
| `docs/使用说明.md` | `documentation/getting-started/user-guide.md` | 用户使用说明 |
| `docs/API.md` | `documentation/technical/api-reference.md` | API 接口文档 |
| `docs/technical_architecture.md` | `documentation/technical/architecture.md` | 技术架构 |
| `docs/优化方向.md` | `documentation/optimization/performance.md` | 性能优化 |
| `docs/optimization_summary.md` | `documentation/optimization/performance.md` | 优化总结 |
| `docs/optimization_checklist.md` | `documentation/optimization/checklist.md` | 优化清单 |
| `docs/optimization-plan.md` | `documentation/optimization/performance.md` | 优化方案 |
| `docs/01-security.md` | `documentation/security/security-config.md` | 安全配置 |
| `docs/02_user_is_active.md` | `documentation/security/permissions.md` | 用户权限 |
| `docs/04_rate_limiting.md` | `documentation/security/security-config.md` | 限流配置 |
| `docs/06_redis_cache.md` | `documentation/optimization/performance.md` | Redis 缓存 |
| `docs/07_bm25_cache.md` | `documentation/optimization/performance.md` | BM25 缓存 |
| `docs/08_db_connection_pool.md` | `documentation/optimization/performance.md` | 连接池优化 |
| `docs/09_alembic_migration.md` | `documentation/development/alembic.md` | 数据库迁移 |
| `docs/10_deep_health_check.md` | `documentation/operations/health-check.md` | 健康检查 |
| `docs/11_global_exception_handler.md` | `documentation/technical/architecture.md` | 异常处理 |
| `docs/15_user_profile.md` | `documentation/getting-started/user-guide.md` | 个人设置 |
| `docs/18_chat_markdown.md` | `documentation/getting-started/user-guide.md` | 对话功能 |
| `docs/19_log_persistence.md` | `documentation/operations/logging.md` | 日志管理 |
| `docs/20_db_backup.md` | `documentation/operations/backup-restore.md` | 数据备份 |
| `docs/RAGAS评测指南.md` | `documentation/evaluation/ragas-guide.md` | 评测指南 |
| `docs/RAGAS评测报告.md` | `documentation/evaluation/ragas-report.md` | 评测报告 |
| `docs/项目演示文档.md` | `documentation/getting-started/project-overview.md` | 项目说明 |
| `docs/admin_system_design.md` | `documentation/security/permissions.md` | 权限设计 |
| `docs/chunk_preview_optimization.md` | `documentation/features/document-preview.md` | 文档预览 |
| `docs/Bug修复历程.md` | `documentation/changelog/README.md` | 更新日志 |
| `docs/技术改进/*.md` | `documentation/changelog/README.md` | 技术改进记录 |

---

## 📊 文档分类

### 按目录分类

```
docs/ (旧)                          documentation/ (新)
├── 使用说明.md                      → getting-started/user-guide.md
├── API.md                          → technical/api-reference.md
├── technical_architecture.md       → technical/architecture.md
├── 优化*.md                        → optimization/
├── 安全相关 (01-06)                → security/
├── 运维相关 (08-20)                → operations/
├── RAGAS评测*.md                   → evaluation/
├── 项目演示文档.md                  → getting-started/project-overview.md
└── 技术改进/                       → changelog/
```

---

## 🔄 迁移建议

### 保留旧文档

旧文档 `docs/` 目录保留，作为历史参考。

### 使用新文档

新文档 `documentation/` 是当前维护的文档，结构更清晰，内容更完整。

### 文档选择

| 场景 | 推荐使用 |
|------|----------|
| 新用户入门 | `documentation/getting-started/` |
| API 开发 | `documentation/technical/api-reference.md` |
| 部署上线 | `documentation/deployment/` |
| 功能开发 | `documentation/features/` |
| 运维管理 | `documentation/operations/` |

---

## 📚 相关文档

- [文档中心](./README.md) - 新文档主索引
- [旧文档目录](../docs/) - 历史文档
