"""认证接口:验证码、注册、登录。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas.auth import (
    CaptchaResponse,
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.security import generate_captcha
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])

# 限频器
limiter = Limiter(key_func=get_remote_address)


@router.get("/captcha", response_model=CaptchaResponse, summary="获取图形验证码")
def get_captcha():
    captcha_id, image = generate_captcha()
    return CaptchaResponse(captcha_id=captcha_id, captcha_image=image)


@router.post("/register", response_model=UserOut, summary="注册")
@limiter.limit("3/minute")  # 每分钟最多3次注册
def register(request: Request, req: RegisterRequest, db: Session = Depends(get_db)):
    return auth_service.register(db, req)


@router.post("/login", response_model=TokenResponse, summary="登录")
@limiter.limit("5/minute")  # 每分钟最多5次登录
def login(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
    return auth_service.login(db, req)


@router.get("/me", summary="当前登录用户信息")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models import Department

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
        "nickname": user.nickname,
        "email": user.email,
        "avatar_url": user.avatar_url,
    }


@router.put("/profile", summary="更新个人信息")
def update_profile(
    nickname: str | None = None,
    email: str | None = None,
    avatar_url: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新当前用户的个人信息。"""
    if nickname is not None:
        user.nickname = nickname
    if email is not None:
        user.email = email
    if avatar_url is not None:
        user.avatar_url = avatar_url
    db.commit()
    db.refresh(user)
    return {"message": "个人信息更新成功"}


@router.post("/change-password", summary="修改密码")
def change_password(
    req: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改当前用户的密码。"""
    from app.security import hash_password, verify_password
    
    if not verify_password(req.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="旧密码错误")
    
    user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"message": "密码修改成功"}
