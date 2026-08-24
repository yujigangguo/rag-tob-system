"""RAGAS 评测管线:准备评测知识库 + 真实检索/生成链路(与线上一致)。"""
from __future__ import annotations

import json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Chunk, Department, Document, KnowledgeBase
from app.rag.embeddings import get_embeddings
from app.rag.llm import get_llm
from app.rag.prompts import RAG_SYSTEM_PROMPT, RAG_USER_PROMPT
from app.rag.retrieval import retrieve_multi_kb
from app.services.chat_service import _map_to_parents
from config.settings import settings

# 评测知识库名称与所属部门(不存在则创建)
EVAL_KB_NAME = "评测知识库"
EVAL_DEPT_NAME = "默认部门"
EVAL_DOCS_DIR = Path("data/raw")
RAW_DOCS = [  # 参与评测的文档(按文件名)
    "员工手册.md",
    "产品说明-星云智能音箱.md",
    "常见问题FAQ.md",
]


def get_or_create_eval_kb(db: Session) -> KnowledgeBase:
    """查找或创建评测知识库(默认部门)。"""
    kb = db.scalar(select(KnowledgeBase).where(KnowledgeBase.name == EVAL_KB_NAME))
    if kb is not None:
        return kb
    dept = db.scalar(select(Department).where(Department.name == EVAL_DEPT_NAME))
    if dept is None:
        dept = Department(name=EVAL_DEPT_NAME)
        db.add(dept)
        db.commit()
        db.refresh(dept)
    kb = KnowledgeBase(
        user_id=_admin_user(db).id,
        name=EVAL_KB_NAME,
        description="RAGAS 评测用知识库(自动创建)",
        department_id=dept.id,
        retrieval_type="hybrid",
        chunk_size=500,
        chunk_overlap=50,
        parent_chunk_size=2000,
    )
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return kb


def ensure_docs_parsed(db: Session, kb_id: int) -> list[int]:
    """确保三份评测文档已上传并解析完成;返回文档 id 列表(已存在则跳过)。"""
    from app.services.document_service import parse_and_index, upload_document

    done_ids: list[int] = []
    for filename in RAW_DOCS:
        src = EVAL_DOCS_DIR / filename
        if not src.exists():
            print(f"  [跳过] 缺少源文件: {src}")
            continue
        existing = db.scalar(
            select(Document).where(
                Document.kb_id == kb_id, Document.filename == filename
            )
        )
        if existing is not None and existing.status == "completed":
            print(f"  [复用] {filename} 已解析")
            done_ids.append(existing.id)
            continue
        # 用 UploadFile 兼容方式上传(直接走 service,不经过 HTTP)
        from io import BytesIO

        from fastapi import UploadFile

        with src.open("rb") as f:
            content = f.read()

        upload = UploadFile(filename=filename, file=BytesIO(content))
        doc = upload_document(db, _admin_user(db), kb_id, upload)
        parse_and_index(db, doc.id)
        db.refresh(doc)
        if doc.status != "completed":
            raise RuntimeError(f"文档解析失败: {filename} -> {doc.error_msg}")
        print(f"  [解析] {filename} 完成,子块数={doc.chunk_count}")
        done_ids.append(doc.id)
    return done_ids


def _admin_user(db: Session):
    """取一个系统管理员(建库/传文档需要管理员权限)。"""
    from app.models import User

    user = db.scalar(select(User).where(User.role == "super_admin"))
    if user is None:
        raise RuntimeError("数据库中不存在 super_admin 用户,请先指派管理员")
    return user


def retrieve_contexts(db: Session, kb_id: int, question: str, top_n: int | None = None) -> list[str]:
    """真实检索链路:向量 + BM25 + RRF -> 子块映射父块,返回上下文列表。"""
    top_n = top_n or settings.final_top_k
    kb = db.get(KnowledgeBase, kb_id)
    child_texts = list(
        db.scalars(
            select(Chunk.content).where(
                Chunk.kb_id == kb_id, Chunk.parent_id.isnot(None)
            )
        ).all()
    )
    if not child_texts:
        raise RuntimeError(f"知识库 {kb_id} 没有已解析的子块,无法检索")
    docs = retrieve_multi_kb(
        [kb_id], get_embeddings(), question,
        {kb_id: child_texts}, {kb_id: kb.retrieval_type},
    )
    parents = _map_to_parents(db, docs)
    return [d.page_content for d in parents[:top_n]]


def generate_answer(question: str, contexts: list[str]) -> str:
    """真实生成链路:与线上一致的提示词调用 qwen-max。"""
    context = "\n\n".join(
        f"[{i}] (来源文档ID: 评测文档)\n{c}" for i, c in enumerate(contexts, 1)
    )
    messages = [
        SystemMessage(content=RAG_SYSTEM_PROMPT),
        HumanMessage(
            content=RAG_USER_PROMPT.format(
                history="（无）", context=context or "（无相关资料）", question=question,
            )
        ),
    ]
    return get_llm().invoke(messages).content


def load_eval_dataset(path: str = "data/ragas_eval.json") -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)
