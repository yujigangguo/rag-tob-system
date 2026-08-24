"""问答功能测试(需要真实 LLM API Key)。"""
from __future__ import annotations

from pathlib import Path

import pytest

from config.settings import settings


def _prepare_kb_with_doc(client, headers, department_id: int, wait_doc_parsed) -> int:
    r = client.post("/api/knowledge-bases", json={
        "name": "问答测试库", "retrieval_type": "hybrid",
        "department_id": department_id,
        "chunk_size": 300, "chunk_overlap": 30,
    }, headers=headers)
    assert r.status_code == 200
    kb_id = r.json()["id"]
    md = Path("data/raw/员工手册.md")
    with md.open("rb") as f:
        r = client.post(f"/api/knowledge-bases/{kb_id}/documents",
                        files={"file": ("员工手册.md", f, "text/markdown")},
                        headers=headers)
    assert r.status_code == 200
    wait_doc_parsed(headers, kb_id, r.json()["id"])
    return kb_id


def test_chat_stream(client, auth_headers, department_id, wait_doc_parsed):
    """流式问答:应返回 SSE 格式并最终给出 [DONE]。"""
    if not settings.llm_api_key:
        pytest.skip("未配置 LLM_API_KEY,跳过问答测试")

    kb_id = _prepare_kb_with_doc(client, auth_headers, department_id, wait_doc_parsed)

    r = client.post("/api/chat/stream", json={
        "question": "年假有几天?",
        "kb_ids": [kb_id],
        "model": settings.llm_model,
        "temperature": 0.7, "top_p": 0.8, "max_tokens": 512, "history_rounds": 5,
    }, headers=auth_headers)
    assert r.status_code == 200
    text = r.text
    assert "data:" in text
    assert "[DONE]" in text

    # 会话应已创建
    r = client.get("/api/chat/sessions", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1

    # 引用映射与知识库来源应随消息持久化(历史消息可恢复引用链接、可追溯检索来源)
    r = client.get(f"/api/chat/sessions/{r.json()[0]['id']}/messages", headers=auth_headers)
    assert r.status_code == 200
    assert any(
        m["role"] == "assistant" and "citations" in m and "kb_ids" in m and m["kb_ids"] == [kb_id]
        for m in r.json()
    )


def test_chat_session_crud(client, auth_headers):
    """会话的创建、重命名、删除。"""
    r = client.post("/api/chat/sessions", json={"name": "我的会话"}, headers=auth_headers)
    assert r.status_code == 200
    session_id = r.json()["id"]

    r = client.put(f"/api/chat/sessions/{session_id}", json={"name": "改名了"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["name"] == "改名了"

    r = client.delete(f"/api/chat/sessions/{session_id}", headers=auth_headers)
    assert r.status_code == 200
