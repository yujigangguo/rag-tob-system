"""向量库读写。

默认 Milvus:
- Milvus Lite:本地单文件、零部署,适合起步(和 Chroma 一样方便,但可平滑迁移到集群);
- 独立部署 / Zilliz Cloud:配置 MILVUS_URI 指向服务地址。

配置 VECTOR_DB_TYPE=chroma / qdrant 可切换回前两者。

另提供 chunk 的 JSON 持久化,供 BM25 等离线场景使用,
避免依赖具体向量库的 get() 实现。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List

from langchain_core.documents import Document

from config.settings import settings

# chunk 文本持久化路径(用于 BM25 索引等)
CHUNKS_JSON = Path(settings.processed_data_dir) / "chunks.json"


def get_vector_store(embeddings=None):
    """根据配置返回向量库实例(Milvus / Chroma / Qdrant)。"""
    if embeddings is None:
        from indexing.embed import get_embeddings

        embeddings = get_embeddings()

    if settings.vector_db_type == "chroma":
        return _get_chroma(embeddings)
    if settings.vector_db_type == "qdrant":
        return _get_qdrant(embeddings)
    return _get_milvus(embeddings)  # 默认 Milvus


def _get_milvus(embeddings):
    """Milvus:本地 Lite 或独立部署 / Zilliz Cloud。

    注意:Milvus Lite 不支持 Windows,Windows 下必须用独立部署(Docker)或 Zilliz Cloud。
    """
    from langchain_milvus import Milvus

    if not settings.milvus_uri and sys.platform == "win32":
        raise RuntimeError(
            "Milvus Lite 不支持 Windows。请改用独立部署或 Zilliz Cloud:"
            "在 .env 中设置 MILVUS_URI(如 http://localhost:19530,需 Docker Desktop),"
            "或 MILVUS_URI=https://xxx.zillizcloud.com 并附带 MILVUS_TOKEN。"
        )

    # uri 为空 -> Milvus Lite 本地文件(macOS/Linux);否则连接独立部署 / Zilliz Cloud
    uri = settings.milvus_uri or settings.milvus_lite_path
    connection_args = {"uri": uri}
    if settings.milvus_token:
        connection_args["token"] = settings.milvus_token

    return Milvus(
        embedding_function=embeddings,
        collection_name=settings.milvus_collection,
        connection_args=connection_args,
        auto_id=True,
        drop_old=False,  # 重建集合时临时设 True(注意会清空旧数据)
    )


def _get_chroma(embeddings):
    from langchain_chroma import Chroma

    return Chroma(
        collection_name="my_kb",
        embedding_function=embeddings,
        persist_directory=settings.chroma_persist_dir,
    )


def _get_qdrant(embeddings):
    from langchain_qdrant import QdrantVectorStore
    from qdrant_client import QdrantClient

    client = QdrantClient(url=settings.qdrant_url)
    return QdrantVectorStore(
        client=client,
        collection_name=settings.qdrant_collection,
        embedding=embeddings,
    )


def add_documents(docs: List[Document], store=None):
    """把(已切分的)文档写入向量库,返回向量库实例。"""
    store = store or get_vector_store()
    store.add_documents(docs)
    return store


def save_chunks(docs: List[Document], path: str | Path | None = None) -> Path:
    """把 chunk 列表持久化为 JSON(供 BM25 等离线使用)。"""
    path = Path(path or CHUNKS_JSON)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [{"page_content": d.page_content, "metadata": d.metadata} for d in docs]
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def load_chunks(path: str | Path | None = None) -> List[Document]:
    """从 JSON 加载 chunk 列表;文件不存在时返回空列表。"""
    path = Path(path or CHUNKS_JSON)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        Document(page_content=item["page_content"], metadata=item.get("metadata") or {})
        for item in data
    ]
