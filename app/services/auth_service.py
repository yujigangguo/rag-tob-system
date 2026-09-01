"""认证业务逻辑:注册、登录。"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.models import Department, User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.security import create_access_token, hash_password, verify_captcha, verify_password

logger = get_logger(__name__)


def register(db: Session, req: RegisterRequest) -> User:
    """用户注册:校验两次密码一致 + 验证码 + 用户名唯一。默认角色 employee。"""
    if req.password != req.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")
    if not verify_captcha(req.captcha_id, req.captcha_code):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")
    exists = db.scalar(select(User).where(User.username == req.username))
    if exists is not None:
        raise HTTPException(status_code=400, detail="该账号名称已被注册")
    # 检查是否是第一个用户，如果是则自动成为超级管理员
    user_count = db.scalar(select(func.count()).select_from(User))
    role = "super_admin" if user_count == 0 else "employee"
    
    user = User(username=req.username, password_hash=hash_password(req.password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("用户注册成功: id=%s username=%s 角色=%s", user.id, user.username, user.role)
    return user


def login(db: Session, req: LoginRequest) -> dict:
    """用户登录:校验验证码 + 账号密码,返回 JWT 与角色/部门信息。"""
    if not verify_captcha(req.captcha_id, req.captcha_code):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")
    user = db.scalar(select(User).where(User.username == req.username))
    if user is None or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=400, detail="账号或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用，请联系管理员")
    token = create_access_token(user.id, user.username)
    dept_name = None
    if user.department_id is not None:
        dept = db.get(Department, user.department_id)
        dept_name = dept.name if dept else None
    logger.info("用户登录成功: id=%s username=%s 角色=%s", user.id, user.username, user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role,
        "department_id": user.department_id,
        "department_name": dept_name,
    }
