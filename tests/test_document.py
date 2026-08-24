"""知识库与文档解析入库测试(含权限:员工只读,管理员可管理)。"""
from __future__ import annotations

import uuid

from pathlib import Path


def _create_kb(client, headers, department_id: int) -> int:
    r = client.post("/api/knowledge-bases", json={
        "name": "测试知识库", "description": "测试", "retrieval_type": "hybrid",
        "department_id": department_id, "chunk_size": 300, "chunk_overlap": 30,
    }, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_kb_create_and_list(client, auth_headers, department_id):
    kb_id = _create_kb(client, auth_headers, department_id)
    r = client.get("/api/knowledge-bases", headers=auth_headers)
    assert r.status_code == 200
    assert any(kb["id"] == kb_id for kb in r.json())


def test_kb_delete(client, auth_headers, department_id):
    kb_id = _create_kb(client, auth_headers, department_id)
    r = client.delete(f"/api/knowledge-bases/{kb_id}", headers=auth_headers)
    assert r.status_code == 200


def test_kb_department_visibility(
    client, auth_headers, department_id, other_department_id, register_user, set_user_department
):
    """部门隔离:普通知识库仅本部门可见,其他部门员工看不到。"""
    kb_id = _create_kb(client, auth_headers, department_id)

    # 其他部门的员工看不到该库
    emp_name = f"emp_b_{uuid.uuid4().hex[:8]}"
    other_headers = register_user(emp_name)
    set_user_department(emp_name, other_department_id)
    r = client.get("/api/knowledge-bases", headers=other_headers)
    assert all(kb["id"] != kb_id for kb in r.json())

    # 本部门员工可以看到该库
    emp_name2 = f"emp_a_{uuid.uuid4().hex[:8]}"
    dept_headers = register_user(emp_name2)
    set_user_department(emp_name2, department_id)
    r = client.get("/api/knowledge-bases", headers=dept_headers)
    assert any(kb["id"] == kb_id for kb in r.json())


def test_public_kb_visible_to_all(
    client, auth_headers, department_id, other_department_id, register_user, set_user_department
):
    """公开知识库:所有部门用户可见,但仅 super_admin 可管理。"""
    r = client.post("/api/knowledge-bases", json={
        "name": "全公司公开库", "department_id": department_id, "is_public": True,
        "retrieval_type": "hybrid", "chunk_size": 300, "chunk_overlap": 30,
    }, headers=auth_headers)
    assert r.status_code == 200, r.text
    pub_kb_id = r.json()["id"]
    assert r.json()["is_public"] is True

    # 其他部门员工可见(可查看)
    emp_name = f"emp_pub_{uuid.uuid4().hex[:8]}"
    emp_headers = register_user(emp_name)
    set_user_department(emp_name, other_department_id)
    r = client.get("/api/knowledge-bases", headers=emp_headers)
    assert any(kb["id"] == pub_kb_id for kb in r.json())

    # 员工不可删除公开库
    r = client.delete(f"/api/knowledge-bases/{pub_kb_id}", headers=emp_headers)
    assert r.status_code in (403, 404)

    # 部门管理员不可删除其他部门的公开库
    dept_admin_name = f"da_{uuid.uuid4().hex[:8]}"
    da_headers = register_user(dept_admin_name)
    set_user_department(dept_admin_name, other_department_id, role="dept_admin")
    r = client.delete(f"/api/knowledge-bases/{pub_kb_id}", headers=da_headers)
    assert r.status_code in (403, 404)

    # 清理
    client.delete(f"/api/knowledge-bases/{pub_kb_id}", headers=auth_headers)


def test_dept_admin_cannot_create_public_kb(client, department_id, register_user, set_user_department):
    """部门管理员不能创建公开知识库。"""
    da_name = f"da_{uuid.uuid4().hex[:8]}"
    da_headers = register_user(da_name)
    set_user_department(da_name, department_id, role="dept_admin")
    r = client.post("/api/knowledge-bases", json={
        "name": "越权公开库", "department_id": department_id, "is_public": True,
        "retrieval_type": "hybrid", "chunk_size": 300, "chunk_overlap": 30,
    }, headers=da_headers)
    assert r.status_code == 403


def test_employee_cannot_create_or_delete_kb(client, department_id, register_user):
    """员工不能创建/删除知识库。"""
    emp_headers = register_user(f"emp_{uuid.uuid4().hex[:8]}")
    r = client.post("/api/knowledge-bases", json={
        "name": "越权库", "department_id": department_id,
        "retrieval_type": "hybrid", "chunk_size": 300, "chunk_overlap": 30,
    }, headers=emp_headers)
    assert r.status_code == 403

    r = client.delete("/api/knowledge-bases/999999", headers=emp_headers)
    assert r.status_code in (403, 404)


def test_upload_parse_and_chunks(client, auth_headers, department_id, wait_doc_parsed):
    """上传离线文件 -> 解析 -> 向量化入 Milvus -> 文档块可查。"""
    kb_id = _create_kb(client, auth_headers, department_id)
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
    wait_doc_parsed(auth_headers, kb_id, doc["id"])

    # 文档列表状态已完成
    r = client.get(f"/api/knowledge-bases/{kb_id}/documents", headers=auth_headers)
    doc = [d for d in r.json() if d["id"] == doc["id"]][0]
    assert doc["status"] == "completed"
    assert doc["chunk_count"] > 0

    # 文档块列表(list_chunks 返回父块;chunk_count 统计的是子块数)
    r = client.get(f"/api/knowledge-bases/{kb_id}/documents/{doc['id']}/chunks",
                   headers=auth_headers)
    assert r.status_code == 200
    chunks = r.json()
    assert len(chunks) >= 1
    assert len(chunks) <= doc["chunk_count"]
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


def test_employee_readonly_documents(
    client, auth_headers, department_id, register_user, set_user_department, wait_doc_parsed
):
    """员工可查看文档/块,但不能上传、编辑、删除。"""
    kb_id = _create_kb(client, auth_headers, department_id)
    md = Path("data/raw/员工手册.md")
    with md.open("rb") as f:
        r = client.post(
            f"/api/knowledge-bases/{kb_id}/documents",
            files={"file": ("员工手册.md", f, "text/markdown")},
            headers=auth_headers,
        )
    assert r.status_code == 200
    doc = r.json()
    wait_doc_parsed(auth_headers, kb_id, doc["id"])

    # 本部门员工:可见但不可管理
    emp_name = f"emp_{uuid.uuid4().hex[:8]}"
    emp_headers = register_user(emp_name)
    set_user_department(emp_name, department_id)
    # 上传被拒
    with md.open("rb") as f:
        r = client.post(
            f"/api/knowledge-bases/{kb_id}/documents",
            files={"file": ("员工手册.md", f, "text/markdown")},
            headers=emp_headers,
        )
    assert r.status_code == 403

    # 可以查看文档与块
    r = client.get(f"/api/knowledge-bases/{kb_id}/documents", headers=emp_headers)
    assert r.status_code == 200
    r = client.get(f"/api/knowledge-bases/{kb_id}/documents/{doc['id']}/chunks", headers=emp_headers)
    assert r.status_code == 200

    # 编辑/删除块被拒(员工无该 KB 可见性时返回 404,有可见性则 403)
    chunks = r.json()
    if chunks:
        r = client.put(f"/api/chunks/{chunks[0]['id']}", json={"content": "x"}, headers=emp_headers)
        assert r.status_code in (403, 404)
        r = client.delete(f"/api/chunks/{chunks[0]['id']}", headers=emp_headers)
        assert r.status_code in (403, 404)

    # 清理知识库
    client.delete(f"/api/knowledge-bases/{kb_id}", headers=auth_headers)
