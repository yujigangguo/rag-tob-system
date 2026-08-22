"""文档业务逻辑:上传、解析、向量化、文档块管理。"""
from __future__ import annotations

import shutil
import threading
from pathlib import Path

from fastapi import HTTPException, UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.models import Chunk, Document, KnowledgeBase
from app.rag.embeddings import get_embeddings
from app.rag.parsers import SUPPORTED_TYPES, is_image, parse_file
from app.rag.vector_store import add_chunks, delete_chunks
from app.services.kb_service import get_kb
from config.settings import settings

logger = get_logger(__name__)

# 文档解析进度(内存):document_id -> 0~100;-1 表示失败
_parse_progress: dict[int, int] = {}


def _set_progress(document_id: int, progress: int) -> None:
    _parse_progress[document_id] = progress


def get_parse_progress(document_id: int) -> dict:
    """查询文档解析进度,返回 {progress, status}。"""
    p = _parse_progress.get(document_id)
    if p is None:
        return {"progress": 0, "status": "pending"}
    if p < 0:
        return {"progress": 0, "status": "failed"}
    if p >= 100:
        return {"progress": 100, "status": "completed"}
    return {"progress": p, "status": "parsing"}


def start_parse_async(document_id: int, chunk_size: int | None = None,
                      chunk_overlap: int | None = None) -> None:
    """在后台线程异步解析文档(上传接口立即返回,不阻塞)。"""
    thread = threading.Thread(
        target=_parse_worker,
        args=(document_id, chunk_size, chunk_overlap),
        daemon=True,
    )
    thread.start()


def _parse_worker(document_id: int, chunk_size: int | None,
                  chunk_overlap: int | None) -> None:
    """后台解析线程:使用独立的 db session。"""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        parse_and_index(db, document_id, chunk_size, chunk_overlap)
    except Exception as e:
        _set_progress(document_id, -1)
        logger.error("后台解析异常: 文档=%s 原因=%s", document_id, e)
    finally:
        db.close()


def _ext(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def upload_document(db: Session, user_id: int, kb_id: int, file: UploadFile) -> Document:
    """保存上传文件并创建文档记录(status=pending)。"""
    kb = get_kb(db, user_id, kb_id)
    ext = _ext(file.filename or "")
    if ext not in SUPPORTED_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: .{ext}")

    save_dir = Path(settings.upload_dir) / str(kb_id)
    save_dir.mkdir(parents=True, exist_ok=True)
    file_path = save_dir / file.filename
    with open(file_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    doc = Document(
        kb_id=kb_id,
        filename=file.filename,
        file_path=str(file_path),
        file_type=ext,
        status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    logger.info("上传文档: kb=%s 文件=%s 类型=%s", kb_id, doc.filename, ext)
    return doc


def parse_and_index(db: Session, document_id: int, chunk_size: int | None = None,
                    chunk_overlap: int | None = None) -> Document:
    """解析文档、切分、向量化写入 Milvus,并落库 chunk 记录。"""
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    kb = db.get(KnowledgeBase, doc.kb_id)
    doc.status = "parsing"
    db.commit()
    _set_progress(document_id, 5)

    try:
        # 图片:暂不解析内容,直接标记完成
        if is_image(doc.file_type):
            doc.status = "completed"
            doc.chunk_count = 0
            doc.error_msg = "图片暂不解析内容(仅保留原文件)"
            db.commit()
            _set_progress(document_id, 100)
            return doc

        text = parse_file(doc.file_path, doc.file_type)
        _set_progress(document_id, 30)
        if not text.strip():
            doc.status = "completed"
            doc.chunk_count = 0
            doc.error_msg = "未解析出文本内容"
            db.commit()
            _set_progress(document_id, 100)
            return doc

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size or kb.chunk_size,
            chunk_overlap=chunk_overlap or kb.chunk_overlap,
            separators=["\n\n", "\n", "。", "!", "?", ";", " ", ""],
        )
        texts = splitter.split_text(text)
        _set_progress(document_id, 50)
        if not texts:
            raise ValueError("切分后无内容")

        embeddings = get_embeddings()
        metadatas = [
            {"kb_id": doc.kb_id, "document_id": document_id, "chunk_index": i}
            for i in range(len(texts))
        ]
        _set_progress(document_id, 60)
        milvus_ids = add_chunks(doc.kb_id, embeddings, texts, metadatas)
        _set_progress(document_id, 90)

        for i, (t, mid) in enumerate(zip(texts, milvus_ids)):
            db.add(Chunk(
                kb_id=doc.kb_id,
                document_id=document_id,
                content=t,
                chunk_index=i,
                milvus_id=str(mid),
            ))

        doc.chunk_count = len(texts)
        doc.status = "completed"
        doc.error_msg = None
        db.commit()
        db.refresh(doc)
        _set_progress(document_id, 100)
        logger.info("文档解析完成: 文档=%s 块数=%s", doc.filename, len(texts))
        return doc
    except Exception as e:
        doc.status = "failed"
        doc.error_msg = str(e)
        db.commit()
        _set_progress(document_id, -1)
        logger.error("文档解析失败: 文档=%s 原因=%s", doc.filename, e)
        raise


def list_documents(db: Session, user_id: int, kb_id: int) -> list[Document]:
    get_kb(db, user_id, kb_id)
    stmt = select(Document).where(Document.kb_id == kb_id).order_by(Document.id.desc())
    return list(db.scalars(stmt).all())


def list_chunks(db: Session, user_id: int, document_id: int) -> list[Chunk]:
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    get_kb(db, user_id, doc.kb_id)
    stmt = select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.chunk_index)
    return list(db.scalars(stmt).all())


def update_chunk(db: Session, user_id: int, chunk_id: int, content: str) -> Chunk:
    """更新文档块:改文本 -> 重新向量化。"""
    chunk = db.get(Chunk, chunk_id)
    if chunk is None:
        raise HTTPException(status_code=404, detail="文档块不存在")
    get_kb(db, user_id, chunk.kb_id)

    embeddings = get_embeddings()
    # 删除旧向量
    if chunk.milvus_id:
        delete_chunks(chunk.kb_id, [chunk.milvus_id])
    # 写入新向量
    new_ids = add_chunks(
        chunk.kb_id, embeddings, [content],
        [{"kb_id": chunk.kb_id, "document_id": chunk.document_id, "chunk_index": chunk.chunk_index}],
    )
    chunk.content = content
    chunk.milvus_id = str(new_ids[0])
    db.commit()
    db.refresh(chunk)
    return chunk


def delete_chunk(db: Session, user_id: int, chunk_id: int) -> None:
    """删除文档块(向量 + 记录)。"""
    chunk = db.get(Chunk, chunk_id)
    if chunk is None:
        raise HTTPException(status_code=404, detail="文档块不存在")
    get_kb(db, user_id, chunk.kb_id)
    if chunk.milvus_id:
        delete_chunks(chunk.kb_id, [chunk.milvus_id])
    db.execute(delete(Chunk).where(Chunk.id == chunk_id))
    db.commit()


def delete_document(db: Session, user_id: int, document_id: int) -> None:
    """删除文档及其所有 chunk(向量 + 记录 + 文件)。"""
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    kb = get_kb(db, user_id, doc.kb_id)

    # 删除该文档所有 chunk 向量
    chunks = list(db.scalars(select(Chunk).where(Chunk.document_id == document_id)).all())
    milvus_ids = [c.milvus_id for c in chunks if c.milvus_id]
    if milvus_ids:
        delete_chunks(doc.kb_id, milvus_ids)

    db.execute(delete(Chunk).where(Chunk.document_id == document_id))
    db.delete(doc)
    if kb.doc_count > 0:
        kb.doc_count -= 1
    db.commit()
    logger.info("删除文档: 文档=%s 块数=%s", doc.filename, len(chunks))
    # 删除本地文件
    try:
        Path(doc.file_path).unlink(missing_ok=True)
    except Exception:
        pass
