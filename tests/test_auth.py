"""认证功能测试:注册、登录、验证码。"""
from __future__ import annotations

import uuid


def _reg_payload(username: str, password: str = "abc123456", confirm: str = "abc123456") -> dict:
    return {
        "username": username, "password": password,
        "confirm_password": confirm, "captcha_id": "x", "captcha_code": "x",
    }


def test_captcha_endpoint(client):
    """验证码接口应返回 id 与 base64 图片。"""
    r = client.get("/api/auth/captcha")
    assert r.status_code == 200
    data = r.json()
    assert data["captcha_id"]
    assert data["captcha_image"].startswith("data:image/png;base64,")


def test_register_success(client):
    username = f"u_{uuid.uuid4().hex[:8]}"
    r = client.post("/api/auth/register", json=_reg_payload(username))
    assert r.status_code == 200, r.text
    assert r.json()["username"] == username


def test_register_password_mismatch(client):
    username = f"u_{uuid.uuid4().hex[:8]}"
    r = client.post("/api/auth/register", json=_reg_payload(username, confirm="different123"))
    assert r.status_code == 400
    assert "密码" in r.json()["detail"]


def test_register_duplicate_username(client):
    username = f"u_{uuid.uuid4().hex[:8]}"
    payload = _reg_payload(username)
    assert client.post("/api/auth/register", json=payload).status_code == 200
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 400
    assert "已" in r.json()["detail"]


def test_login_success(client):
    username = f"u_{uuid.uuid4().hex[:8]}"
    client.post("/api/auth/register", json=_reg_payload(username))
    r = client.post("/api/auth/login", json={
        "username": username, "password": "abc123456",
        "captcha_id": "x", "captcha_code": "x",
    })
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password(client):
    username = f"u_{uuid.uuid4().hex[:8]}"
    client.post("/api/auth/register", json=_reg_payload(username))
    r = client.post("/api/auth/login", json={
        "username": username, "password": "wrong-password",
        "captcha_id": "x", "captcha_code": "x",
    })
    assert r.status_code == 400


def test_protected_endpoint_requires_token(client):
    """未登录访问受保护接口应返回 401。"""
    r = client.get("/api/knowledge-bases")
    assert r.status_code == 401
