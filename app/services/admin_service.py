"""管理后台业务逻辑:用户管理、部门管理、权限管理。"""
from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.models import Department, User
from app.rbac import ALL_ROLES, ROLE_SUPER_ADMIN

logger = get_logger(__name__)


def get_users(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    search: Optional[str] = None,
    role: Optional[str] = None,
    department_id: Optional[int] = None,
) -> dict:
    """获取用户列表（分页、搜索、筛选）。"""
    query = select(User)
    
    # 搜索条件
    if search:
        query = query.where(User.username.ilike(f"%{search}%"))
    if role:
        query = query.where(User.role == role)
    if department_id is not None:
        query = query.where(User.department_id == department_id)
    
    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query)
    
    # 分页查询
    query = query.offset((page - 1) * page_size).limit(page_size)
    users = db.scalars(query).all()
    
    # 转换为字典列表
    items = []
    for user in users:
        dept_name = None
        if user.department_id is not None:
            dept = db.get(Department, user.department_id)
            dept_name = dept.name if dept else None
        
        items.append({
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "department_id": user.department_id,
            "department_name": dept_name,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_user(db: Session, user_id: int) -> dict:
    """获取用户详情。"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    dept_name = None
    if user.department_id is not None:
        dept = db.get(Department, user.department_id)
        dept_name = dept.name if dept else None
    
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "department_id": user.department_id,
        "department_name": dept_name,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def update_user(db: Session, user_id: int, data: dict) -> dict:
    """更新用户信息。"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新字段
    if "username" in data:
        # 检查用户名是否已存在
        existing = db.scalar(select(User).where(User.username == data["username"], User.id != user_id))
        if existing:
            raise HTTPException(status_code=400, detail="用户名已存在")
        user.username = data["username"]
    
    if "role" in data:
        if data["role"] not in ALL_ROLES:
            raise HTTPException(status_code=400, detail="无效的角色")
        user.role = data["role"]
    
    if "department_id" in data:
        if data["department_id"] is not None:
            dept = db.get(Department, data["department_id"])
            if not dept:
                raise HTTPException(status_code=400, detail="部门不存在")
        user.department_id = data["department_id"]
    
    db.commit()
    db.refresh(user)
    logger.info("用户信息更新: id=%s username=%s", user.id, user.username)
    
    return get_user(db, user_id)


def delete_user(db: Session, user_id: int) -> dict:
    """删除用户。"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不能删除自己
    # 这里需要当前用户信息，暂时跳过
    
    username = user.username
    db.delete(user)
    db.commit()
    logger.info("用户已删除: id=%s username=%s", user_id, username)
    
    return {"message": f"用户 {username} 已删除"}


def update_user_role(db: Session, user_id: int, role: str) -> dict:
    """分配用户角色。"""
    if role not in ALL_ROLES:
        raise HTTPException(status_code=400, detail="无效的角色")
    
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.role = role
    db.commit()
    db.refresh(user)
    logger.info("用户角色更新: id=%s username=%s role=%s", user.id, user.username, role)
    
    return get_user(db, user_id)


def update_user_department(db: Session, user_id: int, department_id: Optional[int]) -> dict:
    """分配用户部门。"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if department_id is not None:
        dept = db.get(Department, department_id)
        if not dept:
            raise HTTPException(status_code=400, detail="部门不存在")
    
    user.department_id = department_id
    db.commit()
    db.refresh(user)
    logger.info("用户部门更新: id=%s username=%s department_id=%s", user.id, user.username, department_id)
    
    return get_user(db, user_id)


def toggle_user_active(db: Session, user_id: int, is_active: bool) -> dict:
    """禁用/启用用户。"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    action = "启用" if is_active else "禁用"
    logger.info("用户%s: id=%s username=%s", action, user.id, user.username)
    
    return get_user(db, user_id)


def get_departments(db: Session) -> List[dict]:
    """获取部门列表。"""
    departments = db.scalars(select(Department).order_by(Department.id)).all()
    
    items = []
    for dept in departments:
        # 统计部门下的用户数量
        user_count = db.scalar(select(func.count()).where(User.department_id == dept.id))
        
        items.append({
            "id": dept.id,
            "name": dept.name,
            "user_count": user_count,
            "created_at": dept.created_at.isoformat() if dept.created_at else None,
        })
    
    return items


def create_department(db: Session, name: str) -> dict:
    """创建部门。"""
    # 检查部门名是否已存在
    existing = db.scalar(select(Department).where(Department.name == name))
    if existing:
        raise HTTPException(status_code=400, detail="部门名称已存在")
    
    department = Department(name=name)
    db.add(department)
    db.commit()
    db.refresh(department)
    logger.info("部门创建: id=%s name=%s", department.id, department.name)
    
    return {
        "id": department.id,
        "name": department.name,
        "user_count": 0,
        "created_at": department.created_at.isoformat() if department.created_at else None,
    }


def update_department(db: Session, department_id: int, name: str) -> dict:
    """更新部门。"""
    department = db.get(Department, department_id)
    if not department:
        raise HTTPException(status_code=404, detail="部门不存在")
    
    # 检查部门名是否已存在
    existing = db.scalar(select(Department).where(Department.name == name, Department.id != department_id))
    if existing:
        raise HTTPException(status_code=400, detail="部门名称已存在")
    
    department.name = name
    db.commit()
    db.refresh(department)
    logger.info("部门更新: id=%s name=%s", department.id, department.name)
    
    # 返回更新后的部门信息
    user_count = db.scalar(select(func.count()).where(User.department_id == department.id))
    
    return {
        "id": department.id,
        "name": department.name,
        "user_count": user_count,
        "created_at": department.created_at.isoformat() if department.created_at else None,
    }


def delete_department(db: Session, department_id: int) -> dict:
    """删除部门。"""
    department = db.get(Department, department_id)
    if not department:
        raise HTTPException(status_code=404, detail="部门不存在")
    
    # 检查是否有用户关联
    user_count = db.scalar(select(func.count()).where(User.department_id == department_id))
    if user_count > 0:
        raise HTTPException(status_code=400, detail=f"部门下还有 {user_count} 个用户，无法删除")
    
    name = department.name
    db.delete(department)
    db.commit()
    logger.info("部门已删除: id=%s name=%s", department_id, name)
    
    return {"message": f"部门 {name} 已删除"}


def get_roles() -> List[dict]:
    """获取角色列表。"""
    return [
        {"value": "super_admin", "label": "超级管理员", "description": "系统管理员，拥有所有权限"},
        {"value": "dept_admin", "label": "部门管理员", "description": "部门管理员，管理本部门用户和知识库"},
        {"value": "employee", "label": "普通员工", "description": "普通员工，只能查看本部门知识库"},
    ]


def get_permissions() -> dict:
    """获取权限配置。"""
    return {
        "roles": get_roles(),
        "permissions": {
            "user_management": {
                "super_admin": True,
                "dept_admin": False,
                "employee": False,
            },
            "department_management": {
                "super_admin": True,
                "dept_admin": False,
                "employee": False,
            },
            "knowledge_base_management": {
                "super_admin": "all",
                "dept_admin": "department",
                "employee": False,
            },
            "knowledge_base_view": {
                "super_admin": "all",
                "dept_admin": "department",
                "employee": "department",
            },
        },
    }