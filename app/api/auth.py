"""认证接口:验证码、注册、登录。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas.auth import (
    CaptchaResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.security import generate_captcha
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.get("/captcha", response_model=CaptchaResponse, summary="获取图形验证码")
def get_captcha():
    captcha_id, image = generate_captcha()
    return CaptchaResponse(captcha_id=captcha_id, captcha_image=image)


@router.post("/register", response_model=UserOut, summary="注册")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    return auth_service.register(db, req)


@router.post("/login", response_model=TokenResponse, summary="登录")
def login(req: LoginRequest, db: Session = Depends(get_db)):
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
    }
