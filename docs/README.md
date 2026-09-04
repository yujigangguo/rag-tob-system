# RAG 系统文档目录（归档版）

> ⚠️ **注意**：本文档目录为历史归档版本，当前维护的文档请访问 [documentation/](../documentation/) 目录。

---

## 📁 目录结构

```
docs/
├── README.md                              # 本文件
├── ragas_eval_result.json                 # RAGAS 评测结果数据
│
├── getting-started/                       # 🚀 快速开始
│   ├── 使用说明.md                        # 系统使用说明
│   └── 项目演示文档.md                    # 项目演示
│
├── technical/                             # 🔧 技术文档
│   ├── API.md                             # API 接口文档
│   ├── technical_architecture.md          # 技术架构
│   └── admin_system_design.md             # 管理后台设计
│
├── features/                              # ✨ 功能特性
│   ├── chunk_preview_optimization.md      # 文档块预览优化
│   └── 18_chat_markdown.md                # 对话 Markdown 渲染
│
├── security/                              # 🔒 安全相关
│   ├── 01-security.md                     # 安全配置
│   ├── 02_user_is_active.md               # 用户账号禁用
│   └── 04_rate_limiting.md                # 接口限频
│
├── optimization/                          # 📈 优化相关
│   ├── 优化方向.md                        # 优化方向
│   ├── optimization-plan.md               # 优化方案
│   ├── optimization_summary.md            # 优化总结
│   ├── optimization_checklist.md          # 优化清单
│   ├── 06_redis_cache.md                  # Redis 缓存
│   ├── 07_bm25_cache.md                   # BM25 索引缓存
│   └── 08_db_connection_pool.md           # 数据库连接池
│
├── operations/                            # 🛠️ 运维相关
│   ├── 09_alembic_migration.md            # Alembic 迁移
│   ├── 10_deep_health_check.md            # 深度健康检查
│   ├── 11_global_exception_handler.md     # 全局异常处理
│   ├── 15_user_profile.md                 # 用户个人资料
│   ├── 19_log_persistence.md              # 日志持久化
│   └── 20_db_backup.md                    # 数据库备份
│
├── evaluation/                            # 📊 评测相关
│   ├── RAGAS评测指南.md                   # RAGAS 评测指南
│   └── RAGAS评测报告.md                   # RAGAS 评测报告
│
└── changelog/                             # 📋 更新日志
    ├── Bug修复历程.md                     # Bug 修复记录
    └── 技术改进/                          # 技术改进记录
        ├── README.md
        └── 2026-08-24-*.md                # 各项改进详情
```

---

## 📊 文档统计

| 分类 | 数量 | 说明 |
|------|------|------|
| 快速开始 | 2 篇 | 入门指南 |
| 技术文档 | 3 篇 | 架构与 API |
| 功能特性 | 2 篇 | 功能说明 |
| 安全相关 | 3 篇 | 安全配置 |
| 优化相关 | 7 篇 | 性能优化 |
| 运维相关 | 6 篇 | 运维管理 |
| 评测相关 | 2 篇 | 质量评测 |
| 更新日志 | 7+ 篇 | 版本记录 |
| **合计** | **32+ 篇** | - |

---

## 🔗 新版文档

新版文档已重新整理，结构更清晰：

| 分类 | 新文档位置 |
|------|------------|
| 快速开始 | [documentation/getting-started/](../documentation/getting-started/) |
| 部署方案 | [documentation/deployment/](../documentation/deployment/) |
| 技术文档 | [documentation/technical/](../documentation/technical/) |
| 功能特性 | [documentation/features/](../documentation/features/) |
| 安全权限 | [documentation/security/](../documentation/security/) |
| 性能优化 | [documentation/optimization/](../documentation/optimization/) |
| 运维管理 | [documentation/operations/](../documentation/operations/) |
| 开发文档 | [documentation/development/](../documentation/development/) |
| 评测测试 | [documentation/evaluation/](../documentation/evaluation/) |
| 更新日志 | [documentation/changelog/](../documentation/changelog/) |

---

*最后更新：2024年*
