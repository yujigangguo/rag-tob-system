"""知识库业务逻辑(按部门共享 + 管理员管理)。"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.models import Chunk, Department, Document, KnowledgeBase, User
from app.rbac import ROLE_SUPER_ADMIN, can_manage_kb, can_see_kb, visible_department_ids
from app.rag.vector_store import drop_kb_collection
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate

logger = get_logger(__name__)


def _get(db: Session, kb_id: int) -> KnowledgeBase:
    kb = db.get(KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return kb


def get_kb(db: Session, user: User, kb_id: int) -> KnowledgeBase:
    """获取知识库(可见性校验:仅可见本部门 / 全部)。"""
    kb = _get(db, kb_id)
    if not can_see_kb(user, kb):
        raise HTTPException(status_code=404, detail="知识库不存在")
    return kb


def get_kb_manageable(db: Session, user: User, kb_id: int) -> KnowledgeBase:
    """获取知识库并要求当前用户可管理(增删改/内容管理)。"""
    kb = _get(db, kb_id)
    if not can_see_kb(user, kb):
        raise HTTPException(status_code=404, detail="知识库不存在")
    if not can_manage_kb(user, kb):
        raise HTTPException(status_code=403, detail="无权限:仅管理员可操作该知识库")
    return kb


def create_kb(db: Session, user: User, req: KnowledgeBaseCreate) -> KnowledgeBase:
    """创建知识库:仅管理员;dept_admin 只能在本部门创建普通库,公开库仅 super_admin。"""
    dept_id = req.department_id
    if dept_id is None:
        raise HTTPException(status_code=400, detail="请选择知识库所属部门")
    is_public = req.is_public
    if user.role == ROLE_SUPER_ADMIN:
        pass  # 任意部门;可建公开库
    elif user.role == "dept_admin":
        if dept_id != user.department_id:
            raise HTTPException(status_code=403, detail="只能在本部门创建知识库")
        if is_public:
            raise HTTPException(status_code=403, detail="无权限:仅超级管理员可创建全公司可见的知识库")
    else:
        raise HTTPException(status_code=403, detail="无权限:仅管理员可创建知识库")
    # 校验部门存在
    if db.get(Department, dept_id) is None:
        raise HTTPException(status_code=400, detail="部门不存在")

    data = req.model_dump(exclude={"department_id"})
    kb = KnowledgeBase(user_id=user.id, department_id=dept_id, **data)
    db.add(kb)
    db.commit()
    db.refresh(kb)
    logger.info(
        "创建知识库: id=%s name=%s 部门=%s 公开=%s 检索方式=%s",
        kb.id, kb.name, dept_id, is_public, kb.retrieval_type,
    )
    return kb


def list_kb(db: Session, user: User) -> list[KnowledgeBase]:
    """知识库列表:公开库所有人可见;super_admin 全部;dept_admin / employee 仅本部门普通库。"""
    stmt = select(KnowledgeBase)
    dept_ids = visible_department_ids(user)
    if dept_ids is not None:
        stmt = stmt.where(
            or_(
                KnowledgeBase.is_public.is_(True),
                KnowledgeBase.department_id.in_(dept_ids),
            )
        )
    stmt = stmt.order_by(KnowledgeBase.is_public.desc(), KnowledgeBase.id.desc())
    return list(db.scalars(stmt).all())


def update_kb(db: Session, user: User, kb_id: int, req: KnowledgeBaseUpdate) -> KnowledgeBase:
    """更新知识库:管理员;调整所属部门/公开属性仅 super_admin。"""
    kb = get_kb_manageable(db, user, kb_id)
    data = req.model_dump(exclude_unset=True)
    if "department_id" in data and data["department_id"] != kb.department_id:
        if user.role != ROLE_SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="仅系统管理员可调整知识库所属部门")
        if db.get(Department, data["department_id"]) is None:
            raise HTTPException(status_code=400, detail="部门不存在")
    if "is_public" in data and data["is_public"] != kb.is_public:
        if user.role != ROLE_SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="仅系统管理员可调整知识库公开属性")
    for key, value in data.items():
        setattr(kb, key, value)
    db.commit()
    db.refresh(kb)
    return kb


def delete_kb(db: Session, user: User, kb_id: int) -> None:
    """删除知识库:管理员;删除 Milvus collection 与 MySQL 记录。"""
    kb = get_kb_manageable(db, user, kb_id)
    # 1. 删除 Milvus 中的向量集合
    drop_kb_collection(kb_id)
    # 2. 删除 MySQL 中的 chunk / document 记录(先子块后父块,避免自引用外键冲突)
    db.execute(delete(Chunk).where(Chunk.kb_id == kb_id, Chunk.parent_id.isnot(None)))
    db.execute(delete(Chunk).where(Chunk.kb_id == kb_id))
    db.execute(delete(Document).where(Document.kb_id == kb_id))
    # 3. 删除知识库记录
    db.delete(kb)
    db.commit()
    logger.info("删除知识库: id=%s name=%s", kb_id, kb.name)
