"""知识库与文档解析入库测试。"""
from __future__ import annotations

from pathlib import Path


def _create_kb(client, headers) -> int:
    r = client.post("/api/knowledge-bases", json={
        "name": "测试知识库", "description": "测试", "retrieval_type": "hybrid",
        "chunk_size": 300, "chunk_overlap": 30,
    }, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_kb_create_and_list(client, auth_headers):
    kb_id = _create_kb(client, auth_headers)
    r = client.get("/api/knowledge-bases", headers=auth_headers)
    assert r.status_code == 200
    assert any(kb["id"] == kb_id for kb in r.json())


def test_kb_delete(client, auth_headers):
    kb_id = _create_kb(client, auth_headers)
    r = client.delete(f"/api/knowledge-bases/{kb_id}", headers=auth_headers)
    assert r.status_code == 200


def test_kb_isolation(client, auth_headers):
    """知识库按用户隔离:其他用户不可见。"""
    kb_id = _create_kb(client, auth_headers)
    # 另一个用户
    import uuid
    username = f"other_{uuid.uuid4().hex[:8]}"
    client.post("/api/auth/register", json={
        "username": username, "password": "test123456",
        "confirm_password": "test123456", "captcha_id": "x", "captcha_code": "x",
    })
    r = client.post("/api/auth/login", json={
        "username": username, "password": "test123456",
        "captcha_id": "x", "captcha_code": "x",
    })
    other_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r = client.get("/api/knowledge-bases", headers=other_headers)
    assert all(kb["id"] != kb_id for kb in r.json())


def test_upload_parse_and_chunks(client, auth_headers):
    """上传离线文件 -> 解析 -> 向量化入 Milvus -> 文档块可查。"""
    kb_id = _create_kb(client, auth_headers)
    md = Path("data/raw/员工手册.md")
    assert md.exists(), "缺少测试文件 data/raw/员工手册.md"

    with md.open("rb") as f:
        r = client.post(
            f"/api/knowledge-bases/{kb_id}/documents",
            files={"file": ("员工手册.md", f, "text/markdown")},
            headers=auth_headers,
        )
    assert r.status_code == 200, r.text
    doc = r.json()
    assert doc["status"] == "completed"
    assert doc["chunk_count"] > 0

    # 文档块列表
    r = client.get(f"/api/knowledge-bases/{kb_id}/documents/{doc['id']}/chunks",
                   headers=auth_headers)
    assert r.status_code == 200
    chunks = r.json()
    assert len(chunks) == doc["chunk_count"]
    assert all(c["content"] for c in chunks)

    # 编辑文档块
    chunk_id = chunks[0]["id"]
    r = client.put(f"/api/chunks/{chunk_id}", json={"content": "这是修改后的文档块内容"},
                   headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["content"] == "这是修改后的文档块内容"

    # 删除文档块
    r = client.delete(f"/api/chunks/{chunk_id}", headers=auth_headers)
    assert r.status_code == 200

    # 清理知识库
    client.delete(f"/api/knowledge-bases/{kb_id}", headers=auth_headers)
