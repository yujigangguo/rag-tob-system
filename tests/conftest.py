"""pytest 配置:使用独立测试数据库,关闭验证码,提供 TestClient。"""
from __future__ import annotations

import os

# 必须在 import app 之前设置环境变量
os.environ["CAPTCHA_ENABLED"] = "false"
os.environ["DB_NAME"] = "rag_db_test"
# Milvus collection 前缀隔离:测试用 test_kb_*,避免覆盖/删除开发库的 kb_* 数据
os.environ["MILVUS_COLLECTION_PREFIX"] = "test_kb_"

import pymysql
import pytest
from fastapi.testclient import TestClient

from config.settings import settings


def _ensure_test_db() -> None:
    """重建测试数据库(旧结构可能残留,每次会话先删后建保证 schema 最新)。"""
    conn = pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user="root",
        password="root123456",
    )
    try:
        with conn.cursor() as cur:
            cur.execute("DROP DATABASE IF EXISTS rag_db_test")
            cur.execute("CREATE DATABASE rag_db_test CHARACTER SET utf8mb4")
            cur.execute("GRANT ALL PRIVILEGES ON rag_db_test.* TO 'rag_user'@'%'")
            cur.execute("FLUSH PRIVILEGES")
        conn.commit()
    finally:
        conn.close()


_ensure_test_db()

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

Base.metadata.create_all(bind=engine)

from sqlalchemy import text  # noqa: E402


def _seed_department(name: str) -> int:
    """确保部门存在,返回其 id。"""
    with engine.begin() as c:
        dept_id = c.execute(
            text("SELECT id FROM departments WHERE name = :n"), {"n": name}
        ).scalar()
        if dept_id is None:
            c.execute(text("INSERT INTO departments (name) VALUES (:n)"), {"n": name})
            dept_id = c.execute(
                text("SELECT id FROM departments WHERE name = :n"), {"n": name}
            ).scalar()
        return dept_id


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def department_id() -> int:
    """测试部门(管理员建库用)。"""
    return _seed_department("测试部门")


@pytest.fixture(scope="session")
def other_department_id() -> int:
    """另一个部门(部门隔离断言用)。"""
    return _seed_department("其他部门")


@pytest.fixture(scope="session")
def register_user(client):
    """返回一个函数:注册并登录普通员工用户,返回带 Bearer token 的请求头。"""

    def _register(username: str, password: str = "test123456") -> dict:
        r = client.post("/api/auth/register", json={
            "username": username, "password": password,
            "confirm_password": password, "captcha_id": "x", "captcha_code": "x",
        })
        assert r.status_code == 200, r.text
        r = client.post("/api/auth/login", json={
            "username": username, "password": password,
            "captcha_id": "x", "captcha_code": "x",
        })
        assert r.status_code == 200, r.text
        assert r.json()["role"] == "employee"
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    return _register


@pytest.fixture(scope="session")
def set_user_department():
    """返回一个函数:直接改测试库里某用户的部门归属(按用户名)。"""

    def _set(username: str, dept_id: int, role: str | None = None) -> None:
        with engine.begin() as c:
            if role:
                c.execute(
                    text("UPDATE users SET department_id = :d, role = :r WHERE username = :u"),
                    {"d": dept_id, "r": role, "u": username},
                )
            else:
                c.execute(
                    text("UPDATE users SET department_id = :d WHERE username = :u"),
                    {"d": dept_id, "u": username},
                )

    return _set


@pytest.fixture(scope="session")
def wait_doc_parsed(client):
    """返回函数:轮询文档解析进度直到 completed / failed / 超时。"""

    def _wait(headers: dict, kb_id: int, doc_id: int, timeout: int = 90) -> None:
        import time

        deadline = time.time() + timeout
        while time.time() < deadline:
            r = client.get(
                f"/api/knowledge-bases/{kb_id}/documents/{doc_id}/progress", headers=headers
            )
            assert r.status_code == 200, r.text
            status = r.json()["status"]
            if status == "completed":
                return
            if status == "failed":
                raise AssertionError(f"文档解析失败: {r.json()}")
            time.sleep(0.5)
        raise AssertionError("文档解析超时")

    return _wait


@pytest.fixture(scope="session")
def auth_headers(client) -> dict:
    """注册并登录一个测试用户(提升为超级管理员),返回带 Bearer token 的请求头。"""
    import uuid

    username = f"test_{uuid.uuid4().hex[:8]}"
    r = client.post("/api/auth/register", json={
        "username": username, "password": "test123456",
        "confirm_password": "test123456", "captcha_id": "x", "captcha_code": "x",
    })
    assert r.status_code == 200, r.text
    # 测试用户提升为超级管理员(建库/管理内容需要)
    with engine.begin() as c:
        c.execute(
            text("UPDATE users SET role='super_admin' WHERE username = :u"), {"u": username}
        )
    r = client.post("/api/auth/login", json={
        "username": username, "password": "test123456",
        "captcha_id": "x", "captcha_code": "x",
    })
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "super_admin"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
