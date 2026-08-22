"""知识库业务逻辑。"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.models import Chunk, Document, KnowledgeBase
from app.rag.vector_store import drop_kb_collection
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate

logger = get_logger(__name__)


def get_kb(db: Session, user_id: int, kb_id: int) -> KnowledgeBase:
    """获取属于当前用户的知识库,否则 404。"""
    kb = db.get(KnowledgeBase, kb_id)
    if kb is None or kb.user_id != user_id:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return kb


def create_kb(db: Session, user_id: int, req: KnowledgeBaseCreate) -> KnowledgeBase:
    kb = KnowledgeBase(user_id=user_id, **req.model_dump())
    db.add(kb)
    db.commit()
    db.refresh(kb)
    logger.info("创建知识库: id=%s name=%s 检索方式=%s", kb.id, kb.name, kb.retrieval_type)
    return kb


def list_kb(db: Session, user_id: int) -> list[KnowledgeBase]:
    stmt = (
        select(KnowledgeBase)
        .where(KnowledgeBase.user_id == user_id)
        .order_by(KnowledgeBase.id.desc())
    )
    return list(db.scalars(stmt).all())


def update_kb(db: Session, user_id: int, kb_id: int, req: KnowledgeBaseUpdate) -> KnowledgeBase:
    kb = get_kb(db, user_id, kb_id)
    for key, value in req.model_dump(exclude_unset=True).items():
        setattr(kb, key, value)
    db.commit()
    db.refresh(kb)
    return kb


def delete_kb(db: Session, user_id: int, kb_id: int) -> None:
    kb = get_kb(db, user_id, kb_id)
    # 1. 删除 Milvus 中的向量集合
    drop_kb_collection(kb_id)
    # 2. 删除 MySQL 中的 chunk / document 记录
    db.execute(delete(Chunk).where(Chunk.kb_id == kb_id))
    db.execute(delete(Document).where(Document.kb_id == kb_id))
    # 3. 删除知识库记录
    db.delete(kb)
    db.commit()
    logger.info("删除知识库: id=%s name=%s", kb_id, kb.name)
