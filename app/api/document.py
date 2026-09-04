"""文档与文档块接口。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models import Document, User
from app.schemas.document import (
    ChunkOut,
    ChunkUpdate,
    DocumentOut,
    DocumentVersionOut,
)
from app.services import document_service

# 文档接口(挂在知识库下)
documents_router = APIRouter(prefix="/knowledge-bases/{kb_id}/documents", tags=["文档"])

# 文档块接口(chunk_id 全局唯一,独立路径)
chunks_router = APIRouter(prefix="/chunks", tags=["文档块"])


@documents_router.post("", response_model=DocumentOut, summary="上传文档(仅管理员,后台异步解析)")
def upload(
    kb_id: int,
    file: UploadFile = File(..., description="离线文档"),
    chunk_size: int | None = Form(None, description="切块大小(覆盖知识库默认)"),
    chunk_overlap: int | None = Form(None, description="重叠大小"),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    doc = document_service.upload_document(db, user, kb_id, file)
    # 仅新上传/内容变化(状态 pending)才触发解析;同名同内容去重命中(completed)直接复用
    if doc.status == "pending":
        document_service.start_parse_async(doc.id, chunk_size, chunk_overlap)
    return doc


@documents_router.get("", response_model=list[DocumentOut], summary="文档列表")
def list_documents(kb_id: int, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    return document_service.list_documents(db, user, kb_id)


@documents_router.get("/{document_id}/progress", summary="查询文档解析进度")
def get_progress(document_id: int, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    # 校验文档所属知识库对当前用户可见
    from app.services.kb_service import get_kb
    get_kb(db, user, doc.kb_id)
    return document_service.get_parse_progress(document_id)


@documents_router.delete("/{document_id}", summary="删除文档(仅管理员)")
def delete_document(document_id: int, user: User = Depends(require_admin),
                    db: Session = Depends(get_db)):
    document_service.delete_document(db, user, document_id)
    return {"message": "删除成功"}


@documents_router.post("/batch-delete", summary="批量删除文档(仅管理员)")
def batch_delete_documents(
    kb_id: int,
    document_ids: list[int],
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """批量删除文档。
    
    权限要求：管理员（需有该知识库的管理权限）
    """
    success_count = 0
    failed_ids = []
    
    for doc_id in document_ids:
        try:
            document_service.delete_document(db, user, doc_id)
            success_count += 1
        except Exception as e:
            failed_ids.append({"id": doc_id, "error": str(e)})
    
    return {
        "message": f"成功删除 {success_count} 个文档",
        "success_count": success_count,
        "failed_count": len(failed_ids),
        "failed_ids": failed_ids,
    }


@documents_router.get("/{document_id}/chunks", response_model=list[ChunkOut], summary="文档块列表")
def list_chunks(document_id: int, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    return document_service.list_chunks(db, user, document_id)


@documents_router.get("/{document_id}/versions", response_model=list[DocumentVersionOut],
                      summary="文档版本列表")
def list_versions(document_id: int, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    return document_service.list_document_versions(db, user, document_id)


@documents_router.get("/{document_id}/versions/{version}/chunks", response_model=list[ChunkOut],
                      summary="指定版本的文档块列表(版本对比)")
def get_version_chunks(document_id: int, version: int, user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    return document_service.get_version_chunks(db, user, document_id, version)


@documents_router.post("/{document_id}/rollback", response_model=DocumentOut,
                       summary="回滚到上一版本(仅管理员)")
def rollback(document_id: int, user: User = Depends(require_admin),
             db: Session = Depends(get_db)):
    return document_service.rollback_document(db, user, document_id)


@chunks_router.put("/{chunk_id}", response_model=ChunkOut, summary="编辑文档块(仅管理员)")
def update_chunk(chunk_id: int, req: ChunkUpdate, user: User = Depends(require_admin),
                 db: Session = Depends(get_db)):
    return document_service.update_chunk(db, user, chunk_id, req.content)


@chunks_router.delete("/{chunk_id}", summary="删除文档块(仅管理员)")
def delete_chunk(chunk_id: int, user: User = Depends(require_admin),
                 db: Session = Depends(get_db)):
    document_service.delete_chunk(db, user, chunk_id)
    return {"message": "删除成功"}


@documents_router.get("/{document_id}/preview", summary="文档预览")
def preview_document(
    document_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """预览文档内容（支持 PDF、Word、TXT 等格式）。
    
    返回文档的文本内容或文件流。
    """
    from fastapi.responses import FileResponse, Response
    from pathlib import Path
    
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 校验权限
    from app.services.kb_service import get_kb
    get_kb(db, user, doc.kb_id)
    
    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 根据文件类型返回不同响应
    file_type = doc.file_type.lower()
    
    if file_type == 'pdf':
        # PDF 直接返回文件流
        return FileResponse(
            path=str(file_path),
            media_type='application/pdf',
            filename=doc.filename,
        )
    elif file_type in ['txt', 'md', 'json', 'csv']:
        # 文本文件返回内容
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = file_path.read_text(encoding='gbk', errors='ignore')
        return Response(
            content=content,
            media_type='text/plain; charset=utf-8',
        )
    elif file_type in ['docx', 'doc']:
        # Word 文档解析为文本
        try:
            from app.rag.parsers import parse_file
            text = parse_file(str(file_path), file_type)
            return Response(
                content=text,
                media_type='text/plain; charset=utf-8',
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文档解析失败: {str(e)}")
    elif file_type in ['pptx', 'ppt']:
        # PPT 解析为文本
        try:
            from app.rag.parsers import parse_file
            text = parse_file(str(file_path), file_type)
            return Response(
                content=text,
                media_type='text/plain; charset=utf-8',
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文档解析失败: {str(e)}")
    else:
        # 其他类型返回文件下载
        return FileResponse(
            path=str(file_path),
            filename=doc.filename,
        )
