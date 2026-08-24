"""RBAC 权限模型迁移 + 部门种子脚本(幂等,可重复执行)。

功能:
1. 创建 departments 表(新表,create_all 自动建);
2. 给 users / knowledge_bases 增加 role、department_id 列(已存在则跳过);
3. 预置部门(默认:研发部/市场部/人事部,可用命令行参数自定义);
4. 存量知识库 department_id 为空时回填到"默认部门";
5. 打印角色/部门指派 SQL 示例。

用法:
    uv run python scripts/init_rbac.py                 # 默认部门
    uv run python scripts/init_rbac.py 研发部 市场部 人事部

注意:用户角色/归属需要管理员按需指派(见脚本末尾输出的 SQL 示例)。
"""
from __future__ import annotations

import sys

from sqlalchemy import text

# 确保导入 app 前路径正确
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from app.database import Base, engine  # noqa: E402

DEFAULT_DEPTS = ["研发部", "市场部", "人事部"]
BACKFILL_DEPT = "默认部门"


def _column_exists(conn, table: str, column: str) -> bool:
    row = conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND COLUMN_NAME = :c"
        ),
        {"t": table, "c": column},
    ).scalar()
    return bool(row)


def _ensure_column(conn, table: str, column: str, ddl: str) -> None:
    if _column_exists(conn, table, column):
        print(f"  [跳过] {table}.{column} 已存在")
    else:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
        print(f"  [新增] {table}.{column}")


def main() -> None:
    depts = sys.argv[1:] or DEFAULT_DEPTS
    print("=== RBAC 迁移与部门种子 ===")

    # 1. 建表(新表:departments)
    Base.metadata.create_all(bind=engine)
    print("[完成] 表结构就绪(departments 等新表已创建)")

    with engine.begin() as conn:
        # 2. 加列
        print("--- 增加字段 ---")
        _ensure_column(conn, "users", "role",
                       "VARCHAR(16) NOT NULL DEFAULT 'employee' COMMENT 'super_admin/dept_admin/employee'")
        _ensure_column(conn, "users", "department_id", "INT NULL COMMENT '所属部门 id'")
        _ensure_column(conn, "knowledge_bases", "department_id", "INT NULL COMMENT '所属部门 id'")
        _ensure_column(
            conn, "knowledge_bases", "is_public",
            "TINYINT(1) NOT NULL DEFAULT 0 COMMENT '全公司可见(仅 super_admin 可设)'",
        )

        # 3. 预置部门
        print("--- 预置部门 ---")
        for name in depts + ([BACKFILL_DEPT] if BACKFILL_DEPT not in depts else []):
            exists = conn.execute(
                text("SELECT COUNT(*) FROM departments WHERE name = :n"), {"n": name}
            ).scalar()
            if exists:
                print(f"  [跳过] 部门已存在: {name}")
            else:
                conn.execute(text("INSERT INTO departments (name) VALUES (:n)"), {"n": name})
                print(f"  [新增] 部门: {name}")

        # 4. 存量知识库回填到默认部门
        print("--- 存量知识库回填 ---")
        orphan = conn.execute(
            text("SELECT COUNT(*) FROM knowledge_bases WHERE department_id IS NULL")
        ).scalar()
        if orphan:
            backfill_id = conn.execute(
                text("SELECT id FROM departments WHERE name = :n"), {"n": BACKFILL_DEPT}
            ).scalar()
            conn.execute(
                text("UPDATE knowledge_bases SET department_id = :d WHERE department_id IS NULL"),
                {"d": backfill_id},
            )
            print(f"  [回填] {orphan} 个知识库 -> 部门「{BACKFILL_DEPT}」(id={backfill_id})")
        else:
            print("  [跳过] 无未归属的知识库")

        # 5. 加 NOT NULL 约束(回填完成后)
        if not _column_exists(conn, "knowledge_bases", "department_id"):
            pass  # 上面已加列
        conn.execute(
            text(
                "ALTER TABLE knowledge_bases "
                "MODIFY COLUMN department_id INT NOT NULL COMMENT '所属部门 id'"
            )
        )
        print("[完成] knowledge_bases.department_id 置为 NOT NULL")

    # 6. 输出角色指派示例
    print()
    print("=== 角色/部门指派 SQL 示例(管理员手工执行)===")
    print("-- 系统管理员(super admin,可见所有部门)")
    print("UPDATE users SET role='super_admin' WHERE username='admin';")
    print("-- 部门管理员(如:研发部管理员,部门 id 以实际为准)")
    print("UPDATE users SET role='dept_admin', department_id=1 WHERE username='zhangsan';")
    print("-- 员工归属部门")
    print("UPDATE users SET department_id=1 WHERE username='lisi';")
    print("-- 查看当前用户与角色")
    print("SELECT id, username, role, department_id FROM users;")


if __name__ == "__main__":
    main()
