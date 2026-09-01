"""管理后台相关的 Pydantic 模型。"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    """用户信息输出模型。"""
    id: int
    username: str
    role: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None


class UserListResponse(BaseModel):
    """用户列表响应模型。"""
    items: List[UserOut]
    total: int
    page: int
    page_size: int


class UserUpdateRequest(BaseModel):
    """用户更新请求模型。"""
    username: Optional[str] = Field(None, min_length=2, max_length=64)
    role: Optional[str] = None
    department_id: Optional[int] = None


class UserRoleRequest(BaseModel):
    """用户角色分配请求模型。"""
    role: str = Field(..., description="角色名称")


class UserDepartmentRequest(BaseModel):
    """用户部门分配请求模型。"""
    department_id: Optional[int] = Field(None, description="部门ID")


class DepartmentOut(BaseModel):
    """部门信息输出模型。"""
    id: int
    name: str
    user_count: int = 0
    created_at: Optional[datetime] = None


class DepartmentCreateRequest(BaseModel):
    """部门创建请求模型。"""
    name: str = Field(..., min_length=1, max_length=64)


class DepartmentUpdateRequest(BaseModel):
    """部门更新请求模型。"""
    name: str = Field(..., min_length=1, max_length=64)


class RoleOut(BaseModel):
    """角色信息输出模型。"""
    value: str
    label: str
    description: str


class PermissionOut(BaseModel):
    """权限信息输出模型。"""
    roles: List[RoleOut]
    permissions: dict


class MessageResponse(BaseModel):
    """通用消息响应模型。"""
    message: str


class ResetPasswordRequest(BaseModel):
    """管理员重置密码请求。"""
    new_password: str = Field(..., min_length=6, max_length=64, description="新密码")