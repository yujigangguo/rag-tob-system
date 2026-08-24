"""知识库与文档解析入库测试(含权限:员工只读,管理员可管理)。"""
from __future__ import annotations

import uuid

from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Chunk, Document


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


def _upload_md(client, headers, kb_id: int, filename: str, data: bytes):
    r = client.post(
        f"/api/knowledge-bases/{kb_id}/documents",
        files={"file": (filename, data, "text/markdown")},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    return r.json()


def _child_map(kb_id: int, document_id: int, version: int) -> dict[str, str]:
    """文档某版本子块 {content -> milvus_id}。"""
    db = SessionLocal()
    try:
        chunks = list(db.scalars(
            select(Chunk).where(
                Chunk.kb_id == kb_id,
                Chunk.document_id == document_id,
                Chunk.parent_id.isnot(None),
                Chunk.version == version,
            )
        ).all())
        return {c.content: c.milvus_id for c in chunks}
    finally:
        db.close()


def test_reupload_identical_skips(
    client, auth_headers, department_id, wait_doc_parsed
):
    """同名同内容重传:零消耗复用,不新增文档、doc_count 不变。"""
    kb_id = _create_kb(client, auth_headers, department_id)
    md = Path("data/raw/员工手册.md")
    data = md.read_bytes()

    doc = _upload_md(client, auth_headers, kb_id, "员工手册.md", data)
    wait_doc_parsed(auth_headers, kb_id, doc["id"])

    doc2 = _upload_md(client, auth_headers, kb_id, "员工手册.md", data)
    assert doc2["id"] == doc["id"]  # 复用同一文档记录
    assert doc2["status"] == "completed"  # 直接完成,无需重新解析

    db = SessionLocal()
    try:
        count = len(list(db.scalars(select(Document).where(Document.kb_id == kb_id)).all()))
    finally:
        db.close()
    assert count == 1  # 没有产生重复文档

    r = client.get("/api/knowledge-bases", headers=auth_headers)
    kb = next(k for k in r.json() if k["id"] == kb_id)
    assert kb["doc_count"] == 1  # doc_count 不变


def test_reupload_changed_reuses_unchanged_vectors(
    client, auth_headers, department_id, wait_doc_parsed
):
    """同名不同内容重传:覆盖更新同一文档;未变化的子块复用旧向量,变化部分新嵌入。"""
    kb_id = _create_kb(client, auth_headers, department_id)
    md = Path("data/raw/员工手册.md")
    data = md.read_bytes()

    doc = _upload_md(client, auth_headers, kb_id, "员工手册.md", data)
    wait_doc_parsed(auth_headers, kb_id, doc["id"])
    old_map = _child_map(kb_id, doc["id"], doc["version"])
    assert old_map, "首版应产生子块"

    # 改版:末尾追加一段,其余内容不变
    new_data = data + "\n\n## 新增条款\n\n- 本版本测试新增:年终奖按 2 个月工资发放。".encode("utf-8")
    _upload_md(client, auth_headers, kb_id, "员工手册.md", new_data)
    wait_doc_parsed(auth_headers, kb_id, doc["id"])

    # 解析完成后重新取文档,确认版本 +1(版本号在异步解析中更新)
    r = client.get(f"/api/knowledge-bases/{kb_id}/documents", headers=auth_headers)
    doc2 = next(d for d in r.json() if d["id"] == doc["id"])
    assert doc2["version"] == doc["version"] + 1, "内容变化应生成新版本"

    new_map = _child_map(kb_id, doc["id"], doc2["version"])
    assert new_map, "改版后应产生子块"

    # 未变化的子块:milvus_id 完全复用(不重新嵌入)
    reused = [t for t in old_map if t in new_map]
    assert reused, "应有未变化的子块被复用"
    for t in reused:
        assert old_map[t] == new_map[t], f"未变化子块应复用旧向量: {t[:20]}"

    db = SessionLocal()
    try:
        doc_row = db.get(Document, doc["id"])
        assert doc_row.content_hash is not None  # 记录文件哈希
        count = len(list(db.scalars(select(Document).where(Document.kb_id == kb_id)).all()))
    finally:
        db.close()
    assert count == 1

    # 清理
    client.delete(f"/api/knowledge-bases/{kb_id}", headers=auth_headers)


def test_document_versions_and_rollback(
    client, auth_headers, department_id, wait_doc_parsed
):
    """版本管理:重传生成新版本、旧版本可查看、可回滚。"""
    kb_id = _create_kb(client, auth_headers, department_id)
    md = Path("data/raw/员工手册.md")
    data = md.read_bytes()

    doc = _upload_md(client, auth_headers, kb_id, "员工手册.md", data)
    wait_doc_parsed(auth_headers, kb_id, doc["id"])
    assert doc["version"] == 1
    r = client.get(f"/api/knowledge-bases/{kb_id}/documents/{doc['id']}/chunks", headers=auth_headers)
    v1_parent_count = len(r.json())
    assert v1_parent_count >= 1

    # 改版 -> v2(解析完成后版本才更新)
    new_data = data + "\n\n## 测试新增\n\n- 版本回滚验证内容。".encode("utf-8")
    _upload_md(client, auth_headers, kb_id, "员工手册.md", new_data)
    wait_doc_parsed(auth_headers, kb_id, doc["id"])
    r = client.get(f"/api/knowledge-bases/{kb_id}/documents", headers=auth_headers)
    doc2 = next(d for d in r.json() if d["id"] == doc["id"])
    assert doc2["version"] == 2

    # 当前块列表只返回 v2 父块
    r = client.get(f"/api/knowledge-bases/{kb_id}/documents/{doc2['id']}/chunks", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1

    # 版本列表:v2 当前
    r = client.get(f"/api/knowledge-bases/{kb_id}/documents/{doc2['id']}/versions", headers=auth_headers)
    assert r.status_code == 200
    ver_list = r.json()
    assert [v["version"] for v in ver_list] == [2, 1]
    assert ver_list[0]["is_current"] is True

    # 查看旧版本块
    r = client.get(f"/api/knowledge-bases/{kb_id}/documents/{doc2['id']}/versions/1/chunks",
                   headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == v1_parent_count

    # 回滚 -> v1
    r = client.post(f"/api/knowledge-bases/{kb_id}/documents/{doc2['id']}/rollback",
                    headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["version"] == 1

    # 回滚后当前块列表 = v1 块
    r = client.get(f"/api/knowledge-bases/{kb_id}/documents/{doc2['id']}/chunks", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == v1_parent_count

    # 已是最旧版本,再回滚应报错
    r = client.post(f"/api/knowledge-bases/{kb_id}/documents/{doc2['id']}/rollback",
                    headers=auth_headers)
    assert r.status_code == 400

    # 清理
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
