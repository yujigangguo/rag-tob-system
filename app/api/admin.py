"""管理后台接口:用户管理、部门管理、权限管理。"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.logging_config import get_logger
from app.models import User
from app.rbac import ROLE_SUPER_ADMIN, ROLE_DEPT_ADMIN
from app.schemas.admin import (
    DepartmentCreateRequest,
    DepartmentOut,
    DepartmentUpdateRequest,
    MessageResponse,
    PermissionOut,
    ResetPasswordRequest,
    RoleOut,
    UserDepartmentRequest,
    UserListResponse,
    UserOut,
    UserRoleRequest,
    UserUpdateRequest,
)
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["管理后台"])

logger = get_logger(__name__)


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求超级管理员权限。"""
    if current_user.role != ROLE_SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="需要超级管理员权限")
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求管理员权限（超级管理员或部门管理员）。"""
    if current_user.role not in (ROLE_SUPER_ADMIN, ROLE_DEPT_ADMIN):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


# ==================== 用户管理 ====================

@router.get("/users", response_model=UserListResponse, summary="获取用户列表")
def get_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    role: Optional[str] = Query(None, description="角色筛选"),
    department_id: Optional[int] = Query(None, description="部门ID筛选"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取用户列表（分页、搜索、筛选）。
    
    - **page**: 页码，从1开始
    - **page_size**: 每页数量，1-100
    - **search**: 搜索关键词（用户名）
    - **role**: 角色筛选
    - **department_id**: 部门ID筛选
    
    权限要求：管理员（超级管理员或部门管理员）
    """
    # 部门管理员只能查看本部门用户
    if current_user.role == ROLE_DEPT_ADMIN:
        department_id = current_user.department_id
    
    return admin_service.get_users(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        department_id=department_id,
    )


@router.get("/users/{user_id}", response_model=UserOut, summary="获取用户详情")
def get_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取用户详情。
    
    权限要求：管理员（超级管理员或部门管理员）
    """
    user_data = admin_service.get_user(db, user_id)
    
    # 部门管理员只能查看本部门用户
    if current_user.role == ROLE_DEPT_ADMIN:
        if user_data.get("department_id") != current_user.department_id:
            raise HTTPException(status_code=403, detail="无权访问该用户信息")
    
    return user_data


@router.put("/users/{user_id}", response_model=UserOut, summary="更新用户信息")
def update_user(
    user_id: int,
    req: UserUpdateRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """更新用户信息。
    
    权限要求：超级管理员
    """
    data = req.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="没有需要更新的数据")
    
    return admin_service.update_user(db, user_id, data)


@router.delete("/users/{user_id}", response_model=MessageResponse, summary="删除用户")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """删除用户。
    
    权限要求：超级管理员
    """
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除当前登录用户")
    
    return admin_service.delete_user(db, user_id)


@router.put("/users/{user_id}/role", response_model=UserOut, summary="分配用户角色")
def update_user_role(
    user_id: int,
    req: UserRoleRequest,
    request: Request,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """分配用户角色。
    
    权限要求：超级管理员
    """
    from app.services.audit_service import log_action
    result = admin_service.update_user_role(db, user_id, req.role)
    log_action(
        db, current_user.id, current_user.username,
        "update_role", "user", user_id, result.get("username"),
        f"角色改为 {req.role}", request.client.host if request.client else None
    )
    return result


@router.put("/users/{user_id}/department", response_model=UserOut, summary="分配用户部门")
def update_user_department(
    user_id: int,
    req: UserDepartmentRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """分配用户部门。
    
    权限要求：超级管理员
    """
    return admin_service.update_user_department(db, user_id, req.department_id)


@router.put("/users/{user_id}/status", response_model=UserOut, summary="禁用/启用用户")
def toggle_user_status(
    user_id: int,
    is_active: bool = Query(..., description="true=启用, false=禁用"),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """禁用或启用用户。
    
    权限要求：超级管理员
    """
    # 不能禁用自己
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能禁用当前登录用户")
    
    return admin_service.toggle_user_active(db, user_id, is_active)


@router.post("/users/{user_id}/reset-password", response_model=MessageResponse, summary="重置用户密码")
def reset_user_password(
    user_id: int,
    req: ResetPasswordRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """管理员重置用户密码。
    
    权限要求：超级管理员
    """
    from app.security import hash_password
    
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.password_hash = hash_password(req.new_password)
    db.commit()
    logger.info("管理员重置密码: admin=%s target=%s", current_user.username, user.username)
    return {"message": f"用户 {user.username} 密码已重置"}


# ==================== 部门管理 ====================

@router.get("/departments", response_model=List[DepartmentOut], summary="获取部门列表")
def get_departments(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取部门列表。
    
    权限要求：管理员（超级管理员或部门管理员）
    """
    return admin_service.get_departments(db)


@router.post("/departments", response_model=DepartmentOut, summary="创建部门")
def create_department(
    req: DepartmentCreateRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """创建部门。
    
    权限要求：超级管理员
    """
    return admin_service.create_department(db, req.name)


@router.put("/departments/{department_id}", response_model=DepartmentOut, summary="更新部门")
def update_department(
    department_id: int,
    req: DepartmentUpdateRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """更新部门。
    
    权限要求：超级管理员
    """
    return admin_service.update_department(db, department_id, req.name)


@router.delete("/departments/{department_id}", response_model=MessageResponse, summary="删除部门")
def delete_department(
    department_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """删除部门。
    
    权限要求：超级管理员
    """
    return admin_service.delete_department(db, department_id)


# ==================== 权限管理 ====================

@router.get("/roles", response_model=List[RoleOut], summary="获取角色列表")
def get_roles(
    current_user: User = Depends(require_admin),
):
    """获取角色列表。
    
    权限要求：管理员（超级管理员或部门管理员）
    """
    return admin_service.get_roles()


@router.get("/permissions", response_model=PermissionOut, summary="获取权限配置")
def get_permissions(
    current_user: User = Depends(require_admin),
):
    """获取权限配置。
    
    权限要求：管理员（超级管理员或部门管理员）
    """
    return admin_service.get_permissions()


# ==================== 审计日志 ====================

@router.get("/audit-logs", summary="获取审计日志")
def get_audit_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    action: Optional[str] = Query(None, description="操作类型筛选"),
    username: Optional[str] = Query(None, description="操作人筛选"),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """获取审计日志列表。
    
    权限要求：超级管理员
    """
    from app.services.audit_service import get_audit_logs
    return get_audit_logs(db, page, page_size, action, username)


# ==================== 系统配置 ====================

@router.get("/configs", summary="获取所有系统配置")
def get_system_configs(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """获取所有系统配置。
    
    权限要求：超级管理员
    """
    from app.services.config_service import get_all_configs
    return get_all_configs(db)


@router.put("/configs/{key}", summary="更新系统配置")
def update_system_config(
    key: str,
    value: str = Query(..., description="配置值"),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """更新系统配置。
    
    权限要求：超级管理员
    """
    from app.services.config_service import update_config
    return update_config(db, key, value)


# ==================== 仪表盘统计 ====================

@router.get("/dashboard", summary="获取仪表盘统计数据")
def get_dashboard_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取管理后台仪表盘统计数据。
    
    权限要求：管理员
    """
    from sqlalchemy import func
    
    # 用户统计
    total_users = db.scalar(select(func.count()).select_from(User))
    active_users = db.scalar(select(func.count()).where(User.is_active == True))
    
    # 知识库统计
    from app.models import KnowledgeBase, Document, ChatSession, ChatMessage
    total_kbs = db.scalar(select(func.count()).select_from(KnowledgeBase))
    total_docs = db.scalar(select(func.count()).select_from(Document))
    
    # 对话统计
    total_sessions = db.scalar(select(func.count()).select_from(ChatSession))
    total_messages = db.scalar(select(func.count()).select_from(ChatMessage))
    
    # 最近7天注册用户
    from datetime import datetime, timedelta
    week_ago = datetime.now() - timedelta(days=7)
    new_users_week = db.scalar(
        select(func.count()).where(User.created_at >= week_ago)
    )
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "new_this_week": new_users_week,
        },
        "knowledge_bases": {
            "total": total_kbs,
        },
        "documents": {
            "total": total_docs,
        },
        "conversations": {
            "sessions": total_sessions,
            "messages": total_messages,
        },
    }