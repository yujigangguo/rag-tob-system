"""切分策略:把长文档切成适合检索的块。

采用递归字符切分,优先按段落/句子边界切,再退回字符级,
chunk_size 与 chunk_overlap 从配置读取。
"""
from __future__ import annotations

from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import settings


def build_splitter() -> RecursiveCharacterTextSplitter:
    """构建切分器。separators 优先级从高到低。"""
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", "。", "!", "?", ";", " ", ""],
    )


def split_documents(docs: List[Document]) -> List[Document]:
    """对清洗后的文档切分,自动保留元数据(来源、页码等)。"""
    splitter = build_splitter()
    return splitter.split_documents(docs)
