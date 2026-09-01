"""管理后台接口:用户管理、部门管理、权限管理。"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.rbac import ROLE_SUPER_ADMIN, ROLE_DEPT_ADMIN
from app.schemas.admin import (
    DepartmentCreateRequest,
    DepartmentOut,
    DepartmentUpdateRequest,
    MessageResponse,
    PermissionOut,
    RoleOut,
    UserDepartmentRequest,
    UserListResponse,
    UserOut,
    UserRoleRequest,
    UserUpdateRequest,
)
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["管理后台"])


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
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """分配用户角色。
    
    权限要求：超级管理员
    """
    return admin_service.update_user_role(db, user_id, req.role)


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