"""数据清洗:统一空白、去页眉页脚残留、去重、丢弃空块。"""
from __future__ import annotations

import re
from typing import List

from langchain_core.documents import Document


def clean_text(text: str) -> str:
    """基础清洗:统一换行、压缩多余空行、去除行首尾空白。"""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)          # 压缩行内多余空格
    text = re.sub(r"\n{3,}", "\n\n", text)       # 压缩多余空行
    lines = [ln.strip() for ln in text.split("\n")]
    return "\n".join(lines).strip()


def remove_duplicates(docs: List[Document]) -> List[Document]:
    """按文本内容去重(保留第一次出现)。"""
    seen = set()
    result: List[Document] = []
    for doc in docs:
        key = doc.page_content.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(doc)
    return result


def clean_documents(docs: List[Document]) -> List[Document]:
    """完整清洗流水线:清洗 -> 丢弃空块 -> 去重。"""
    cleaned: List[Document] = []
    for doc in docs:
        doc.page_content = clean_text(doc.page_content)
        if doc.page_content:
            cleaned.append(doc)
    return remove_duplicates(cleaned)
