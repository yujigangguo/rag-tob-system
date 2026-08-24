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
    kb.doc_count += 1  # 与 delete_document 的 doc_count -= 1 对应
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

        # 父子分块:父块(大粒度,存上下文) -> 子块(小粒度,做检索向量化)
        child_size = chunk_size or kb.chunk_size
        parent_size = kb.parent_chunk_size or 2000
        if parent_size < child_size:
            parent_size = child_size * 4

        overlap = chunk_overlap or kb.chunk_overlap
        separators = ["\n\n", "\n", "。", "!", "?", ";", " ", ""]

        parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=parent_size, chunk_overlap=overlap, separators=separators,
        )
        parents = parent_splitter.split_text(text)
        if not parents:
            raise ValueError("切分后无内容")

        child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=child_size, chunk_overlap=overlap, separators=separators,
        )

        embeddings = get_embeddings()
        total_children = 0
        _set_progress(document_id, 40)

        for parent_idx, parent_text in enumerate(parents):
            # 1) 写父块记录(不写入 Milvus)
            parent = Chunk(
                kb_id=doc.kb_id,
                document_id=document_id,
                content=parent_text,
                chunk_index=parent_idx,
                parent_id=None,
                milvus_id=None,
            )
            db.add(parent)
            db.flush()  # 拿到父块自增 id

            # 2) 父块内切子块
            children = child_splitter.split_text(parent_text) or [parent_text]

            # 3) 子块写入 Milvus(metadata 带 parent_id,检索后映射父块)
            child_metadatas = [
                {"kb_id": doc.kb_id, "document_id": document_id,
                 "parent_id": parent.id, "chunk_index": ci}
                for ci in range(len(children))
            ]
            milvus_ids = add_chunks(doc.kb_id, embeddings, children, child_metadatas)

            # 4) 子块落库
            for ci, (ct, mid) in enumerate(zip(children, milvus_ids)):
                db.add(Chunk(
                    kb_id=doc.kb_id,
                    document_id=document_id,
                    content=ct,
                    chunk_index=ci,
                    parent_id=parent.id,
                    milvus_id=str(mid),
                ))
                total_children += 1

            _set_progress(document_id, 40 + int(50 * (parent_idx + 1) / len(parents)))

        doc.chunk_count = total_children  # 记录子块数(检索单元)
        doc.status = "completed"
        doc.error_msg = None
        db.commit()
        db.refresh(doc)
        _set_progress(document_id, 100)
        logger.info(
            "文档解析完成: 文档=%s 父块=%s 子块=%s",
            doc.filename, len(parents), total_children,
        )
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
    """文档块列表(父子分块:仅返回父块,父块是语义单位)。"""
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    get_kb(db, user_id, doc.kb_id)
    stmt = (
        select(Chunk)
        .where(Chunk.document_id == document_id, Chunk.parent_id.is_(None))
        .order_by(Chunk.chunk_index)
    )
    return list(db.scalars(stmt).all())


def update_chunk(db: Session, user_id: int, chunk_id: int, content: str) -> Chunk:
    """编辑父块:更新文本 -> 删除旧子块 -> 重新切分并向量化。"""
    parent = db.get(Chunk, chunk_id)
    if parent is None:
        raise HTTPException(status_code=404, detail="文档块不存在")
    get_kb(db, user_id, parent.kb_id)
    kb = db.get(KnowledgeBase, parent.kb_id)

    # 1. 删除旧子块(向量 + 记录)
    children = list(db.scalars(select(Chunk).where(Chunk.parent_id == parent.id)).all())
    old_ids = [c.milvus_id for c in children if c.milvus_id]
    if old_ids:
        delete_chunks(parent.kb_id, old_ids)
    db.execute(delete(Chunk).where(Chunk.parent_id == parent.id))

    # 2. 更新父块文本
    parent.content = content
    db.flush()

    # 3. 重新切分子块并向量化
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=kb.chunk_size, chunk_overlap=kb.chunk_overlap,
        separators=["\n\n", "\n", "。", "!", "?", ";", " ", ""],
    )
    children_texts = splitter.split_text(content) or [content]
    embeddings = get_embeddings()
    metas = [
        {"kb_id": parent.kb_id, "document_id": parent.document_id,
         "parent_id": parent.id, "chunk_index": i}
        for i in range(len(children_texts))
    ]
    milvus_ids = add_chunks(parent.kb_id, embeddings, children_texts, metas)
    for i, (ct, mid) in enumerate(zip(children_texts, milvus_ids)):
        db.add(Chunk(
            kb_id=parent.kb_id, document_id=parent.document_id,
            content=ct, chunk_index=i, parent_id=parent.id, milvus_id=str(mid),
        ))

    db.commit()
    db.refresh(parent)
    logger.info("编辑文档块: 父块=%s 重切子块=%s", parent.id, len(children_texts))
    return parent


def delete_chunk(db: Session, user_id: int, chunk_id: int) -> None:
    """删除文档块(父块连同其子块与向量一并删除)。"""
    chunk = db.get(Chunk, chunk_id)
    if chunk is None:
        raise HTTPException(status_code=404, detail="文档块不存在")
    get_kb(db, user_id, chunk.kb_id)

    # 删除子块向量
    children = list(db.scalars(select(Chunk).where(Chunk.parent_id == chunk.id)).all())
    milvus_ids = [c.milvus_id for c in children if c.milvus_id]
    if milvus_ids:
        delete_chunks(chunk.kb_id, milvus_ids)
    # 若当前块本身是子块(有父块),也删自身向量
    if chunk.milvus_id:
        delete_chunks(chunk.kb_id, [chunk.milvus_id])

    db.execute(delete(Chunk).where(Chunk.parent_id == chunk.id))
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
