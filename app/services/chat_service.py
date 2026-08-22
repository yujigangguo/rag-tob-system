"""对话业务逻辑:会话管理与流式问答。"""
from __future__ import annotations

from typing import Generator, List

from fastapi import HTTPException
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.models import ChatMessage, ChatSession, Chunk, KnowledgeBase
from app.rag.embeddings import get_embeddings
from app.rag.llm import get_llm
from app.rag.prompts import RAG_SYSTEM_PROMPT, RAG_USER_PROMPT
from app.rag.retrieval import retrieve_multi_kb
from app.schemas.chat import ChatRequest
from config.settings import settings

logger = get_logger(__name__)


def _get_session(db: Session, user_id: int, session_id: int) -> ChatSession:
    s = db.get(ChatSession, session_id)
    if s is None or s.user_id != user_id:
        raise HTTPException(status_code=404, detail="会话不存在")
    return s


def create_session(db: Session, user_id: int, name: str = "新对话") -> ChatSession:
    s = ChatSession(user_id=user_id, name=name or "新对话")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def list_sessions(db: Session, user_id: int) -> list[ChatSession]:
    stmt = select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.id.desc())
    return list(db.scalars(stmt).all())


def rename_session(db: Session, user_id: int, session_id: int, name: str) -> ChatSession:
    s = _get_session(db, user_id, session_id)
    s.name = name
    db.commit()
    db.refresh(s)
    return s


def delete_session(db: Session, user_id: int, session_id: int) -> None:
    s = _get_session(db, user_id, session_id)
    db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
    db.delete(s)
    db.commit()


def list_messages(db: Session, user_id: int, session_id: int) -> list[ChatMessage]:
    _get_session(db, user_id, session_id)
    stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.id)
    return list(db.scalars(stmt).all())


def _build_history(db: Session, session_id: int, rounds: int) -> str:
    """取最近 N 轮历史消息,组织成文本。"""
    limit = rounds * 2  # 每轮 = 用户 + 助手
    msgs = list(
        db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.desc())
            .limit(limit)
        ).all()
    )
    msgs.reverse()
    return "\n".join(f"{'用户' if m.role == 'user' else '助手'}: {m.content}" for m in msgs)


def _build_context(docs: List[Document]) -> str:
    parts = []
    for i, d in enumerate(docs, 1):
        src = d.metadata.get("document_id", "未知文档")
        parts.append(f"[{i}] (来源文档ID: {src})\n{d.page_content}")
    return "\n\n".join(parts)


def prepare_answer(db: Session, user_id: int, req: ChatRequest) -> dict:
    """检索 + 保存用户消息 + 构造 messages(在请求线程内完成)。"""
    # 1. 会话(不存在则新建)
    if req.session_id is not None:
        session = _get_session(db, user_id, req.session_id)
        session_id = session.id
    else:
        session_id = create_session(db, user_id, req.session_name or "新对话").id

    # 2. 历史对话
    history = _build_history(db, session_id, req.history_rounds)

    # 3. 检索(校验知识库归属)
    kbs = list(
        db.scalars(
            select(KnowledgeBase).where(
                KnowledgeBase.id.in_(req.kb_ids),
                KnowledgeBase.user_id == user_id,
            )
        ).all()
    )
    if not kbs:
        raise HTTPException(status_code=400, detail="未选择有效的知识库")

    kb_chunks: dict[int, List[str]] = {}
    kb_types: dict[int, str] = {}
    for kb in kbs:
        chunks = list(db.scalars(select(Chunk.content).where(Chunk.kb_id == kb.id)).all())
        kb_chunks[kb.id] = chunks
        kb_types[kb.id] = kb.retrieval_type

    docs = retrieve_multi_kb(
        [kb.id for kb in kbs], get_embeddings(), req.question, kb_chunks, kb_types
    )
    logger.info("问答检索: session=%s 知识库=%s 召回=%s 条", session_id, [kb.id for kb in kbs], len(docs))
    context = _build_context(docs[: settings.final_top_k])

    # 4. 保存用户消息
    db.add(ChatMessage(session_id=session_id, role="user", content=req.question))
    db.commit()

    # 5. 构造 messages
    messages = [
        SystemMessage(content=RAG_SYSTEM_PROMPT),
        HumanMessage(content=RAG_USER_PROMPT.format(
            history=history or "（无）", context=context or "（无相关资料）", question=req.question,
        )),
    ]
    return {"session_id": session_id, "messages": messages, "context": context}


def stream_answer(messages: list, session_id: int, req: ChatRequest) -> Generator[str, None, None]:
    """流式生成(逐 token yield),结束后独立会话保存助手消息。"""
    from app.database import SessionLocal

    llm = get_llm(
        model=req.model,
        temperature=req.temperature,
        top_p=req.top_p,
        max_tokens=req.max_tokens,
        streaming=True,
    )

    full: List[str] = []
    for chunk in llm.stream(messages):
        token = chunk.content or ""
        if token:
            full.append(token)
            yield token

    # 流结束后,用独立会话保存助手消息
    db = SessionLocal()
    try:
        db.add(ChatMessage(session_id=session_id, role="assistant", content="".join(full)))
        db.commit()
    finally:
        db.close()
    logger.info("问答生成完成: session=%s 长度=%s 字符", session_id, len("".join(full)))
