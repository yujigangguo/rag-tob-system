"""Redis 客户端:验证码缓存、会话缓存等。"""
from __future__ import annotations

import os
from typing import Optional

import redis

from app.logging_config import get_logger

logger = get_logger(__name__)

# Redis 连接(可选,未配置时使用内存存储)
_redis: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    """获取 Redis 连接,未配置返回 None。"""
    global _redis
    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        return None
    if _redis is None:
        try:
            _redis = redis.from_url(redis_url, decode_responses=True)
            _redis.ping()
            logger.info("Redis 连接成功: %s", redis_url.split("@")[-1])
        except Exception as e:
            logger.warning("Redis 连接失败,使用内存存储: %s", e)
            _redis = None
    return _redis


def set_captcha(captcha_id: str, code: str, expire_seconds: int = 300) -> None:
    """存储验证码。"""
    r = get_redis()
    if r:
        try:
            r.setex(f"captcha:{captcha_id}", expire_seconds, code)
        except Exception as e:
            logger.warning("Redis 存储验证码失败: %s", e)
    else:
        # 内存存储 fallback
        from app.security import _captcha_store
        import time
        _captcha_store[captcha_id] = {
            "code": code,
            "expire": time.time() + expire_seconds,
        }


def get_captcha(captcha_id: str) -> Optional[str]:
    """获取验证码(一次性,获取后删除)。"""
    r = get_redis()
    if r:
        try:
            code = r.get(f"captcha:{captcha_id}")
            if code:
                r.delete(f"captcha:{captcha_id}")
            return code
        except Exception as e:
            logger.warning("Redis 获取验证码失败: %s", e)
    else:
        # 内存存储 fallback
        from app.security import _captcha_store
        import time
        item = _captcha_store.pop(captcha_id, None)
        if item and time.time() <= item["expire"]:
            return item["code"]
    return None
