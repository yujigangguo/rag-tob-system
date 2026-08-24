"""角色与权限:常量、判定助手。

角色模型(三级):
- super_admin  系统管理员:可见/管理所有部门的知识库
- dept_admin   部门管理员:管理本部门所有知识库
- employee     员工(默认):仅可见本部门知识库,可查看与问答,不能管理内容
"""
from __future__ import annotations

from app.models import KnowledgeBase, User

ROLE_SUPER_ADMIN = "super_admin"
ROLE_DEPT_ADMIN = "dept_admin"
ROLE_EMPLOYEE = "employee"

ALL_ROLES = (ROLE_SUPER_ADMIN, ROLE_DEPT_ADMIN, ROLE_EMPLOYEE)


def is_admin(user: User) -> bool:
    """是否管理员(系统管理员 / 部门管理员)。"""
    return user.role in (ROLE_SUPER_ADMIN, ROLE_DEPT_ADMIN)


def can_manage_kb(user: User, kb: KnowledgeBase) -> bool:
    """能否管理该知识库(创建/删除/编辑/内容管理)。

    - super_admin:所有部门
    - dept_admin:仅本部门
    - employee:不可
    """
    if user.role == ROLE_SUPER_ADMIN:
        return True
    if user.role == ROLE_DEPT_ADMIN:
        return user.department_id is not None and kb.department_id == user.department_id
    return False


def can_see_kb(user: User, kb: KnowledgeBase) -> bool:
    """能否看到/使用该知识库(查看、问答)。"""
    if user.role == ROLE_SUPER_ADMIN:
        return True
    return user.department_id is not None and kb.department_id == user.department_id


def visible_department_ids(user: User) -> list[int] | None:
    """可见部门 id 列表;返回 None 表示所有部门(仅 super_admin)。"""
    if user.role == ROLE_SUPER_ADMIN:
        return None
    return [user.department_id] if user.department_id is not None else []
