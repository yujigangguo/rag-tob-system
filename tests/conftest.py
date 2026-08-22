"""pytest 配置:使用独立测试数据库,关闭验证码,提供 TestClient。"""
from __future__ import annotations

import os

# 必须在 import app 之前设置环境变量
os.environ["CAPTCHA_ENABLED"] = "false"
os.environ["DB_NAME"] = "rag_db_test"

import pymysql
import pytest
from fastapi.testclient import TestClient

from config.settings import settings


def _ensure_test_db() -> None:
    """用 root 账号创建测试数据库(不存在时)。"""
    conn = pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user="root",
        password="root123456",
    )
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE DATABASE IF NOT EXISTS rag_db_test CHARACTER SET utf8mb4")
            cur.execute("GRANT ALL PRIVILEGES ON rag_db_test.* TO 'rag_user'@'%'")
            cur.execute("FLUSH PRIVILEGES")
        conn.commit()
    finally:
        conn.close()


_ensure_test_db()

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def auth_headers(client) -> dict:
    """注册并登录一个测试用户,返回带 Bearer token 的请求头。"""
    import uuid

    username = f"test_{uuid.uuid4().hex[:8]}"
    r = client.post("/api/auth/register", json={
        "username": username, "password": "test123456",
        "confirm_password": "test123456", "captcha_id": "x", "captcha_code": "x",
    })
    assert r.status_code == 200, r.text
    r = client.post("/api/auth/login", json={
        "username": username, "password": "test123456",
        "captcha_id": "x", "captcha_code": "x",
    })
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
