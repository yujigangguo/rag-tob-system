"""数据接入层:把各种来源统一加载成 LangChain 的 Document 对象。

支持:PDF / Word(.docx) / 纯文本 / Markdown / 网页 / 目录批量。
所有 loader 统一返回 list[Document],后续清洗、切分、入库都在此基础上进行。
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List

from langchain_core.documents import Document

from config.settings import settings


def load_pdf(path: str | Path) -> List[Document]:
    """加载 PDF(文本型;扫描件需先 OCR)。"""
    from langchain_community.document_loaders import PyPDFLoader

    return PyPDFLoader(str(path)).load()


def load_docx(path: str | Path) -> List[Document]:
    """加载 Word 文档。"""
    from langchain_community.document_loaders import Docx2txtLoader

    return Docx2txtLoader(str(path)).load()


def load_text(path: str | Path) -> List[Document]:
    """加载 txt / md 等纯文本。"""
    from langchain_community.document_loaders import TextLoader

    return TextLoader(str(path), encoding="utf-8").load()


def load_web(url: str) -> List[Document]:
    """加载网页(自动解析正文)。"""
    from langchain_community.document_loaders import WebBaseLoader

    return WebBaseLoader(url).load()


# 扩展名 -> loader 映射(新增来源在此扩展)
_LOADER_MAP: Dict[str, Callable] = {
    ".pdf": load_pdf,
    ".docx": load_docx,
    ".txt": load_text,
    ".md": load_text,
}


def load_file(path: str | Path) -> List[Document]:
    """根据扩展名自动选择 loader。"""
    p = Path(path)
    ext = p.suffix.lower()
    if ext not in _LOADER_MAP:
        raise ValueError(f"暂不支持的格式: {ext}")
    return _LOADER_MAP[ext](p)


def load_directory(dir_path: str | Path | None = None) -> List[Document]:
    """批量加载目录下所有支持的文件(递归)。

    :param dir_path: 目标目录,默认使用配置中的 raw_data_dir。
    """
    root = Path(dir_path or settings.raw_data_dir)
    docs: List[Document] = []
    if not root.exists():
        raise FileNotFoundError(f"数据目录不存在: {root}")
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in _LOADER_MAP:
            try:
                docs.extend(load_file(p))
            except Exception as e:  # 单个文件失败不阻断整体
                print(f"[跳过] {p}: {e}")
    return docs
