"""向量化:通义 embedding(DashScope 原生接口)，带缓存支持。"""
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from typing import List

from langchain_core.embeddings import Embeddings

from app.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)

# Embedding 缓存（内存 + 可选 Redis）
_embedding_cache: dict[str, List[float]] = {}
_CACHE_MAX_SIZE = 10000  # 最多缓存 10000 个文本的 embedding


def _get_cache_key(text: str) -> str:
    """生成缓存键（文本的 MD5 哈希）。"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _get_from_cache(text: str) -> List[float] | None:
    """从缓存获取 embedding。"""
    # 先尝试内存缓存
    cache_key = _get_cache_key(text)
    if cache_key in _embedding_cache:
        return _embedding_cache[cache_key]
    
    # 再尝试 Redis 缓存
    try:
        from app.redis_client import get_redis
        r = get_redis()
        if r:
            cached = r.get(f"embedding:{cache_key}")
            if cached:
                return json.loads(cached)
    except Exception:
        pass
    
    return None


def _set_to_cache(text: str, embedding: List[float]) -> None:
    """存储 embedding 到缓存。"""
    cache_key = _get_cache_key(text)
    
    # 内存缓存（带大小限制）
    if len(_embedding_cache) >= _CACHE_MAX_SIZE:
        # 删除最旧的一半缓存
        keys_to_remove = list(_embedding_cache.keys())[:_CACHE_MAX_SIZE // 2]
        for key in keys_to_remove:
            del _embedding_cache[key]
    _embedding_cache[cache_key] = embedding
    
    # Redis 缓存（可选）
    try:
        from app.redis_client import get_redis
        r = get_redis()
        if r:
            r.setex(
                f"embedding:{cache_key}",
                3600 * 24,  # 缓存 24 小时
                json.dumps(embedding)
            )
    except Exception:
        pass


class CachedDashScopeEmbeddings(Embeddings):
    """带缓存的通义 Embedding 封装。"""
    
    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key
        self._inner = None
    
    @property
    def inner(self):
        """延迟初始化内部 Embedding 实例。"""
        if self._inner is None:
            from langchain_community.embeddings import DashScopeEmbeddings
            self._inner = DashScopeEmbeddings(
                model=self.model,
                dashscope_api_key=self.api_key,
            )
        return self._inner
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量 embedding（带缓存）。"""
        results = [None] * len(texts)
        texts_to_embed = []
        indices_to_embed = []
        
        # 1. 先从缓存获取
        for i, text in enumerate(texts):
            cached = _get_from_cache(text)
            if cached is not None:
                results[i] = cached
            else:
                texts_to_embed.append(text)
                indices_to_embed.append(i)
        
        # 2. 批量 embedding 未缓存的文本
        if texts_to_embed:
            logger.debug("Embedding 缓存命中: %d/%d", len(texts) - len(texts_to_embed), len(texts))
            new_embeddings = self.inner.embed_documents(texts_to_embed)
            
            # 3. 存入缓存并填入结果
            for i, embedding in zip(indices_to_embed, new_embeddings):
                _set_to_cache(texts[i], embedding)
                results[i] = embedding
        else:
            logger.debug("Embedding 缓存全部命中: %d", len(texts))
        
        return results
    
    def embed_query(self, text: str) -> List[float]:
        """单条 embedding（带缓存）。"""
        cached = _get_from_cache(text)
        if cached is not None:
            return cached
        
        embedding = self.inner.embed_query(text)
        _set_to_cache(text, embedding)
        return embedding


@lru_cache
def get_embeddings() -> Embeddings:
    """返回单例 embedding 实例（带缓存的通义 text-embedding）。"""
    return CachedDashScopeEmbeddings(
        model=settings.embedding_model,
        api_key=settings.embedding_api_key,
    )
