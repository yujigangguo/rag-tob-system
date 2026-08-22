"""安全模块:密码哈希、JWT、图形验证码。"""
from __future__ import annotations

import base64
import hashlib
import io
import random
import string
import time
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from PIL import Image, ImageDraw, ImageFont

from config.settings import settings

# 内存中的验证码存储(单机部署够用;生产可替换为 Redis)
_captcha_store: dict[str, dict] = {}


def _prepare_password(password: str) -> bytes:
    """sha256 预处理密码,规避 bcrypt 的 72 字节长度限制。"""
    return hashlib.sha256(password.encode("utf-8")).digest()


def hash_password(password: str) -> str:
    """对密码做 bcrypt 哈希。"""
    return bcrypt.hashpw(_prepare_password(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文密码与哈希是否匹配。"""
    try:
        return bcrypt.checkpw(_prepare_password(plain), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: int, username: str) -> str:
    """签发 JWT access token。"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "username": username, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict | None:
    """解析并校验 JWT,失败返回 None。"""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def generate_captcha() -> tuple[str, str]:
    """生成图形验证码。

    返回 (captcha_id, base64 data URL)。验证码有效期见配置。
    """
    code = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=settings.captcha_length)
    )
    captcha_id = f"cap_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    _captcha_store[captcha_id] = {
        "code": code,
        "expire": time.time() + settings.captcha_expire_seconds,
    }
    return captcha_id, _render_captcha_image(code)


def verify_captcha(captcha_id: str, code: str) -> bool:
    """校验验证码(一次性,校验后即失效)。"""
    if not settings.captcha_enabled:
        return True  # 测试/开发环境可关闭验证码
    item = _captcha_store.pop(captcha_id, None)
    if not item:
        return False
    if time.time() > item["expire"]:
        return False
    return item["code"].upper() == (code or "").strip().upper()


def _render_captcha_image(code: str) -> str:
    """用 Pillow 绘制验证码图片,返回 base64 data URL。"""
    width, height = 130, 42
    image = Image.new("RGB", (width, height), (245, 247, 252))
    draw = ImageDraw.Draw(image)

    # 干扰线
    for _ in range(6):
        draw.line(
            (random.randint(0, width), random.randint(0, height),
             random.randint(0, width), random.randint(0, height)),
            fill=(random.randint(140, 210), random.randint(140, 210), random.randint(140, 210)),
            width=1,
        )

    # 字体:优先 Windows 系统字体,失败则用默认
    font = None
    for path in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"):
        try:
            font = ImageFont.truetype(path, 28)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    # 逐字符绘制(带随机位移,增加辨识难度)
    for i, ch in enumerate(code):
        x = 12 + i * 28
        y = random.randint(4, 10)
        color = (random.randint(20, 120), random.randint(20, 120), random.randint(20, 120))
        draw.text((x, y), ch, fill=color, font=font)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
