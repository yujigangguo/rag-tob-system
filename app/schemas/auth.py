"""认证相关 schema。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class CaptchaResponse(BaseModel):
    captcha_id: str
    captcha_image: str  # base64 data URL


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32, description="账号名称")
    password: str = Field(..., min_length=6, max_length=64, description="密码")
    confirm_password: str = Field(..., min_length=6, max_length=64, description="确认密码")
    captcha_id: str = Field(..., description="验证码标识")
    captcha_code: str = Field(..., description="验证码输入")


class LoginRequest(BaseModel):
    username: str = Field(..., description="账号名称")
    password: str = Field(..., description="密码")
    captcha_id: str = Field(..., description="验证码标识")
    captcha_code: str = Field(..., description="验证码输入")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str = "employee"            # super_admin / dept_admin / employee
    department_id: int | None = None
    department_name: str | None = None


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    department_id: int | None

    model_config = {"from_attributes": True}
