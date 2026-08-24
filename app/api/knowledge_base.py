"""知识库接口。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models import User
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseOut,
    KnowledgeBaseUpdate,
)
from app.services import kb_service

router = APIRouter(prefix="/knowledge-bases", tags=["知识库"])


@router.post("", response_model=KnowledgeBaseOut, summary="创建知识库(仅管理员)")
def create(req: KnowledgeBaseCreate, user: User = Depends(require_admin),
           db: Session = Depends(get_db)):
    return kb_service.create_kb(db, user, req)


@router.get("", response_model=list[KnowledgeBaseOut], summary="知识库列表(按部门可见)")
def list_kb(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return kb_service.list_kb(db, user)


@router.get("/{kb_id}", response_model=KnowledgeBaseOut, summary="知识库详情")
def get_kb(kb_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return kb_service.get_kb(db, user, kb_id)


@router.put("/{kb_id}", response_model=KnowledgeBaseOut, summary="更新知识库(仅管理员)")
def update(kb_id: int, req: KnowledgeBaseUpdate, user: User = Depends(require_admin),
           db: Session = Depends(get_db)):
    return kb_service.update_kb(db, user, kb_id, req)


@router.delete("/{kb_id}", summary="删除知识库(仅管理员)")
def delete(kb_id: int, user: User = Depends(require_admin),
           db: Session = Depends(get_db)):
    kb_service.delete_kb(db, user, kb_id)
    return {"message": "删除成功"}
