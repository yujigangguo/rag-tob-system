"""文档业务逻辑:上传、解析、向量化、文档块管理。"""
from __future__ import annotations

import hashlib
import threading
from pathlib import Path

from fastapi import HTTPException, UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.models import Chunk, Document, KnowledgeBase, User
from app.rag.embeddings import get_embeddings
from app.rag.parsers import SUPPORTED_TYPES, is_image, parse_file
from app.rag.vector_store import add_chunks, delete_chunks
from app.services.kb_service import get_kb, get_kb_manageable
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


def _sha256(text: str) -> str:
    """文本 SHA-256(子块内容哈希,增量更新复用向量用)。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def upload_document(db: Session, user: User, kb_id: int, file: UploadFile) -> Document:
    """保存上传文件并创建文档记录(status=pending)。仅管理员可操作。

    增量更新:
    - 同名文件且内容哈希一致(已完成)→ 直接复用,不重复解析;
    - 同名文件内容变化 → 覆盖更新同一文档记录(解析时按块哈希复用未变化向量)。
    """
    kb = get_kb_manageable(db, user, kb_id)
    ext = _ext(file.filename or "")
    if ext not in SUPPORTED_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: .{ext}")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    # 快速预检:nginx 已转发 Content-Length,超限直接拒绝
    if file.size and file.size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"文件过大:最大支持 {settings.max_upload_size_mb}MB",
        )

    save_dir = Path(settings.upload_dir) / str(kb_id)
    save_dir.mkdir(parents=True, exist_ok=True)
    file_path = save_dir / file.filename

    # 流式写入并计数,防止无 Content-Length 时绕过预检;同时计算文件 SHA-256
    size = 0
    hasher = hashlib.sha256()
    try:
        with open(file_path, "wb") as out:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"文件过大:最大支持 {settings.max_upload_size_mb}MB",
                    )
                out.write(chunk)
                hasher.update(chunk)
    except HTTPException:
        file_path.unlink(missing_ok=True)  # 清理已写入的部分
        raise
    file_hash = hasher.hexdigest()

    # ---- 增量更新:同名文件处理 ----
    existing = db.scalar(
        select(Document).where(Document.kb_id == kb_id, Document.filename == file.filename)
    )
    if existing is not None:
        if existing.content_hash == file_hash and existing.status == "completed":
            logger.info("文档内容无变化,跳过解析: 文档=%s", existing.filename)
            return existing  # 零消耗复用,doc_count 不变
        # 同名但内容变化(或上次解析失败):覆盖更新同一文档记录
        existing.file_path = str(file_path)
        existing.file_type = ext
        existing.content_hash = file_hash
        existing.status = "pending"
        existing.error_msg = None
        _set_progress(existing.id, 0)  # 重置进度,避免前端读到上一次解析的遗留 completed
        db.commit()
        db.refresh(existing)
        logger.info(
            "覆盖更新文档: kb=%s 文件=%s 类型=%s 大小=%sKB",
            kb_id, existing.filename, ext, size // 1024,
        )
        return existing

    doc = Document(
        kb_id=kb_id,
        filename=file.filename,
        file_path=str(file_path),
        file_type=ext,
        status="pending",
        content_hash=file_hash,
    )
    db.add(doc)
    kb.doc_count += 1  # 与 delete_document 的 doc_count -= 1 对应
    _set_progress(doc.id, 0)
    db.commit()
    db.refresh(doc)
    logger.info("上传文档: kb=%s 文件=%s 类型=%s 大小=%sKB", kb_id, doc.filename, ext, size // 1024)
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

        # ---- 增量更新:内存中保留旧子块(内容哈希 -> milvus_id),用于复用未变化的向量 ----
        old_children = list(db.scalars(
            select(Chunk).where(Chunk.document_id == document_id, Chunk.parent_id.isnot(None))
        ).all())
        old_hash_to_milvus: dict[str, str] = {}
        for oc in old_children:
            if oc.content_hash and oc.milvus_id:
                old_hash_to_milvus.setdefault(oc.content_hash, oc.milvus_id)
        reused_milvus_ids: set[str] = set()
        new_chunk_ids: list[int] = []   # 本次新建的 chunk 行(失败时回滚)
        new_milvus_ids: list[str] = []  # 本次新嵌入的向量(失败时回滚)
        reused_count = 0
        # 版本:首版为 1;覆盖更新时新块写入新版本,旧版本块保留(支持回滚)
        new_version = doc.version + 1 if old_children else doc.version

        try:
            for parent_idx, parent_text in enumerate(parents):
                # 1) 写父块记录(不写入 Milvus)
                parent = Chunk(
                    kb_id=doc.kb_id,
                    document_id=document_id,
                    content=parent_text,
                    chunk_index=parent_idx,
                    parent_id=None,
                    milvus_id=None,
                    version=new_version,
                )
                db.add(parent)
                db.flush()  # 拿到父块自增 id

                # 2) 父块内切子块
                children = child_splitter.split_text(parent_text) or [parent_text]

                # 3) 逐子块判定:内容哈希命中旧块 -> 复用旧向量;否则待嵌入
                to_embed: list[str] = []
                to_embed_meta: list[dict] = []
                milvus_for: list[str | None] = [None] * len(children)
                for ci, ct in enumerate(children):
                    h = _sha256(ct)
                    mid = old_hash_to_milvus.pop(h, None) if h else None
                    if mid:
                        milvus_for[ci] = mid
                        reused_milvus_ids.add(mid)
                        reused_count += 1
                    else:
                        to_embed.append(ct)
                        to_embed_meta.append({
                            "kb_id": doc.kb_id, "document_id": document_id,
                            "parent_id": parent.id, "chunk_index": ci,
                        })

                new_ids: list[str] = []
                if to_embed:
                    new_ids = add_chunks(doc.kb_id, embeddings, to_embed, to_embed_meta)
                    new_milvus_ids.extend(new_ids)

                # 4) 子块落库(reused 复用旧 milvus_id,未命中用新嵌入 id)
                embed_iter = iter(new_ids)
                added_chunks: list[Chunk] = []
                for ci, ct in enumerate(children):
                    mid = milvus_for[ci] or str(next(embed_iter))
                    c = Chunk(
                        kb_id=doc.kb_id,
                        document_id=document_id,
                        content=ct,
                        chunk_index=ci,
                        parent_id=parent.id,
                        milvus_id=mid,
                        content_hash=_sha256(ct),
                        version=new_version,
                    )
                    db.add(c)
                    added_chunks.append(c)
                db.flush()  # 拿到本次子块 id(用于失败回滚)
                new_chunk_ids.extend(c.id for c in added_chunks)
                total_children += len(children)

                _set_progress(document_id, 40 + int(50 * (parent_idx + 1) / len(parents)))
        except Exception:
            # 解析失败:回滚本次新建的行与向量,旧版本数据保持可用
            if new_chunk_ids:
                db.execute(delete(Chunk).where(Chunk.id.in_(new_chunk_ids)))
            if new_milvus_ids:
                try:
                    delete_chunks(doc.kb_id, new_milvus_ids)
                except Exception:
                    pass
            db.commit()
            raise

        # 旧版本 chunk 行与向量全部保留(版本管理与回滚);被复用向量跨版本共享,不重复删除
        doc.version = new_version
        doc.chunk_count = total_children  # 记录当前版本子块数(检索单元)
        doc.status = "completed"
        doc.error_msg = None
        db.commit()
        db.refresh(doc)
        _set_progress(document_id, 100)
        logger.info(
            "文档解析完成: 文档=%s 版本=%s 父块=%s 子块=%s 复用向量=%s",
            doc.filename, new_version, len(parents), total_children, reused_count,
        )
        return doc
    except Exception as e:
        doc.status = "failed"
        doc.error_msg = str(e)
        db.commit()
        _set_progress(document_id, -1)
        logger.error("文档解析失败: 文档=%s 原因=%s", doc.filename, e)
        raise


def list_documents(db: Session, user: User, kb_id: int) -> list[Document]:
    get_kb(db, user, kb_id)
    stmt = select(Document).where(Document.kb_id == kb_id).order_by(Document.id.desc())
    return list(db.scalars(stmt).all())


def list_chunks(db: Session, user: User, document_id: int) -> list[Chunk]:
    """文档块列表(父子分块:仅返回当前版本的父块,父块是语义单位)。"""
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    get_kb(db, user, doc.kb_id)
    stmt = (
        select(Chunk)
        .where(
            Chunk.document_id == document_id,
            Chunk.parent_id.is_(None),
            Chunk.version == doc.version,
        )
        .order_by(Chunk.chunk_index)
    )
    return list(db.scalars(stmt).all())


def list_document_versions(db: Session, user: User, document_id: int) -> list[dict]:
    """文档版本列表:[{version, chunk_count, created_at}],用于版本查看与回滚。"""
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    get_kb(db, user, doc.kb_id)
    rows = db.execute(
        select(Chunk.version, func.count(Chunk.id))
        .where(Chunk.document_id == document_id, Chunk.parent_id.is_(None))
        .group_by(Chunk.version)
        .order_by(Chunk.version.desc())
    ).all()
    versions = [
        {"version": v, "parent_count": cnt} for v, cnt in rows
    ]
    # 当前版本标记(可能还没有块,如解析失败)
    for item in versions:
        item["is_current"] = item["version"] == doc.version
    if not any(v["version"] == doc.version for v in versions):
        versions.insert(0, {"version": doc.version, "parent_count": 0, "is_current": True})
    return versions


def get_version_chunks(db: Session, user: User, document_id: int, version: int) -> list[Chunk]:
    """指定版本的父块列表(版本对比 / 查看旧版内容)。"""
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    get_kb(db, user, doc.kb_id)
    stmt = (
        select(Chunk)
        .where(
            Chunk.document_id == document_id,
            Chunk.parent_id.is_(None),
            Chunk.version == version,
        )
        .order_by(Chunk.chunk_index)
    )
    return list(db.scalars(stmt).all())


def rollback_document(db: Session, user: User, document_id: int) -> Document:
    """回滚到上一版本:删除当前版本块与独有向量,恢复上一版本为当前版本。仅管理员。"""
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    get_kb_manageable(db, user, doc.kb_id)
    if doc.version <= 1:
        raise HTTPException(status_code=400, detail="已是第一个版本,无法回滚")

    current_version = doc.version
    target_version = current_version - 1

    # 1. 当前版本块(先子块后父块)
    cur_children = list(db.scalars(
        select(Chunk).where(
            Chunk.document_id == document_id,
            Chunk.parent_id.isnot(None),
            Chunk.version == current_version,
        )
    ).all())
    cur_parents = list(db.scalars(
        select(Chunk).where(
            Chunk.document_id == document_id,
            Chunk.parent_id.is_(None),
            Chunk.version == current_version,
        )
    ).all())
    if cur_children:
        db.execute(delete(Chunk).where(Chunk.id.in_([c.id for c in cur_children])))
    if cur_parents:
        db.execute(delete(Chunk).where(Chunk.id.in_([c.id for c in cur_parents])))

    # 2. 删除当前版本独有向量(被其他版本复用的保留)
    cur_milvus_ids = {c.milvus_id for c in cur_children if c.milvus_id}
    remaining_ids = set(db.scalars(
        select(Chunk.milvus_id).where(
            Chunk.document_id == document_id, Chunk.milvus_id.isnot(None)
        )
    ).all())
    stale = cur_milvus_ids - remaining_ids
    if stale:
        delete_chunks(doc.kb_id, sorted(stale))

    # 3. 切换当前版本
    doc.version = target_version
    doc.chunk_count = len(list(db.scalars(
        select(Chunk).where(
            Chunk.document_id == document_id,
            Chunk.parent_id.isnot(None),
            Chunk.version == target_version,
        )
    ).all()))
    db.commit()
    db.refresh(doc)
    logger.info("文档回滚: 文档=%s 版本 %s -> %s", doc.filename, current_version, target_version)
    return doc


def update_chunk(db: Session, user: User, chunk_id: int, content: str) -> Chunk:
    """编辑父块:更新文本 -> 删除旧子块 -> 重新切分并向量化。仅管理员可操作。"""
    parent = db.get(Chunk, chunk_id)
    if parent is None:
        raise HTTPException(status_code=404, detail="文档块不存在")
    get_kb_manageable(db, user, parent.kb_id)
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

    # 3. 重新切分子块并向量化(继承文档当前版本)
    doc = db.get(Document, parent.document_id)
    doc_version = doc.version if doc else 1
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
            content_hash=_sha256(ct), version=doc_version,
        ))

    db.commit()
    db.refresh(parent)
    logger.info("编辑文档块: 父块=%s 重切子块=%s", parent.id, len(children_texts))
    return parent


def delete_chunk(db: Session, user: User, chunk_id: int) -> None:
    """删除文档块(父块连同其子块与向量一并删除)。仅管理员可操作。"""
    chunk = db.get(Chunk, chunk_id)
    if chunk is None:
        raise HTTPException(status_code=404, detail="文档块不存在")
    get_kb_manageable(db, user, chunk.kb_id)

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


def delete_document(db: Session, user: User, document_id: int) -> None:
    """删除文档及其所有 chunk(向量 + 记录 + 文件)。仅管理员可操作。"""
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    kb = get_kb_manageable(db, user, doc.kb_id)

    # 删除该文档所有 chunk 向量
    chunks = list(db.scalars(select(Chunk).where(Chunk.document_id == document_id)).all())
    milvus_ids = [c.milvus_id for c in chunks if c.milvus_id]
    if milvus_ids:
        delete_chunks(doc.kb_id, milvus_ids)

    db.execute(delete(Chunk).where(Chunk.document_id == document_id, Chunk.parent_id.isnot(None)))
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
