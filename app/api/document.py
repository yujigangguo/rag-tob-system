"""文档与文档块接口。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Document, User
from app.schemas.document import ChunkOut, ChunkUpdate, DocumentOut
from app.services import document_service

# 文档接口(挂在知识库下)
documents_router = APIRouter(prefix="/knowledge-bases/{kb_id}/documents", tags=["文档"])

# 文档块接口(chunk_id 全局唯一,独立路径)
chunks_router = APIRouter(prefix="/chunks", tags=["文档块"])


@documents_router.post("", response_model=DocumentOut, summary="上传文档(后台异步解析)")
def upload(
    kb_id: int,
    file: UploadFile = File(..., description="离线文档"),
    chunk_size: int | None = Form(None, description="切块大小(覆盖知识库默认)"),
    chunk_overlap: int | None = Form(None, description="重叠大小"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = document_service.upload_document(db, user.id, kb_id, file)
    # 后台异步解析,接口立即返回;进度通过 /progress 接口查询
    document_service.start_parse_async(doc.id, chunk_size, chunk_overlap)
    return doc


@documents_router.get("", response_model=list[DocumentOut], summary="文档列表")
def list_documents(kb_id: int, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    return document_service.list_documents(db, user.id, kb_id)


@documents_router.get("/{document_id}/progress", summary="查询文档解析进度")
def get_progress(document_id: int, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    # 校验文档归属当前用户的知识库
    from app.services.kb_service import get_kb
    get_kb(db, user.id, doc.kb_id)
    return document_service.get_parse_progress(document_id)


@documents_router.delete("/{document_id}", summary="删除文档")
def delete_document(document_id: int, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    document_service.delete_document(db, user.id, document_id)
    return {"message": "删除成功"}


@documents_router.get("/{document_id}/chunks", response_model=list[ChunkOut], summary="文档块列表")
def list_chunks(document_id: int, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    return document_service.list_chunks(db, user.id, document_id)


@chunks_router.put("/{chunk_id}", response_model=ChunkOut, summary="编辑文档块")
def update_chunk(chunk_id: int, req: ChunkUpdate, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    return document_service.update_chunk(db, user.id, chunk_id, req.content)


@chunks_router.delete("/{chunk_id}", summary="删除文档块")
def delete_chunk(chunk_id: int, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    document_service.delete_chunk(db, user.id, chunk_id)
    return {"message": "删除成功"}
