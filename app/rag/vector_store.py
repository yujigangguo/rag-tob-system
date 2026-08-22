"""Milvus 向量库:每个知识库一个 collection。"""
from __future__ import annotations

from typing import List

from pymilvus import MilvusClient

from config.settings import settings


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
