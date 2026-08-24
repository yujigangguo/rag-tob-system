"""Milvus 向量库:每个知识库一个 collection。"""
from __future__ import annotations

from typing import List

from pymilvus import DataType, MilvusClient

from config.settings import settings

# chunk 写入 Milvus 的 metadata 字段。
# 显式声明 schema:建库时固定字段结构与类型,不依赖"首次插入的 metadata 隐式推断"。
# 否则一旦 collection 是旧结构(例如缺 parent_id)就会插入失败,或字段被静默丢弃。
MILVUS_METADATA_FIELDS = ("kb_id", "document_id", "parent_id", "chunk_index")


def _metadata_schema() -> dict:
    """每次调用新建一份 schema 字典(避免 langchain-milvus 内部 pop 修改共享对象)。"""
    return {name: {"dtype": DataType.INT64} for name in MILVUS_METADATA_FIELDS}


def kb_collection_name(kb_id: int) -> str:
    """知识库对应的 collection 名。"""
    return f"{settings.milvus_collection_prefix}{kb_id}"


def get_milvus_client() -> MilvusClient:
    """获取 Milvus 客户端(管理用:建删集合、按主键删除)。"""
    kwargs: dict = {"uri": settings.milvus_uri}
    if settings.milvus_token:
        kwargs["token"] = settings.milvus_token
    return MilvusClient(**kwargs)


def get_vector_store(kb_id: int, embeddings):
    """获取某个知识库的 langchain-milvus 向量库实例。"""
    from langchain_milvus import Milvus

    connection_args: dict = {"uri": settings.milvus_uri}
    if settings.milvus_token:
        connection_args["token"] = settings.milvus_token

    return Milvus(
        embedding_function=embeddings,
        collection_name=kb_collection_name(kb_id),
        connection_args=connection_args,
        auto_id=True,
        metadata_schema=_metadata_schema(),
    )


def add_chunks(kb_id: int, embeddings, texts: List[str], metadatas: List[dict]) -> List[str]:
    """批量写入 chunk,返回对应的 Milvus 主键 id 列表。"""
    store = get_vector_store(kb_id, embeddings)
    return store.add_texts(texts, metadatas=metadatas)


def delete_chunks(kb_id: int, milvus_ids: List[str]) -> None:
    """按 Milvus 主键删除 chunk 向量。"""
    if not milvus_ids:
        return
    client = get_milvus_client()
    client.delete(kb_collection_name(kb_id), ids=milvus_ids)


def drop_kb_collection(kb_id: int) -> None:
    """删除知识库对应的 collection。"""
    client = get_milvus_client()
    name = kb_collection_name(kb_id)
    if client.has_collection(name):
        client.drop_collection(name)
