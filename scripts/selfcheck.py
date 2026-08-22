"""环境自检:检查依赖、配置、向量库连通性。

用法(在项目根目录执行):
    uv run python scripts/selfcheck.py
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中(支持从任意目录运行脚本)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def check_imports():
    """检查关键依赖是否可正常导入。"""
    modules = [
        "langchain", "langchain_community", "langchain_openai",
        "langchain_text_splitters", "langchain_milvus",
        "pymilvus", "rank_bm25", "dashscope",
        "fastapi", "uvicorn", "pydantic", "pydantic_settings",
        "pypdf", "docx",
    ]
    for m in modules:
        try:
            importlib.import_module(m)
            print(f"  [OK]   {m}")
        except Exception as e:
            print(f"  [FAIL] {m}: {e}")


def check_config():
    """检查配置是否就绪。"""
    from config.settings import settings

    print(f"  LLM:       {settings.llm_model}  key={'已配置' if settings.llm_api_key else '未配置'}")
    print(f"  Embedding: {settings.embedding_model}  key={'已配置' if settings.embedding_api_key else '未配置'}")
    print(f"  向量库:    {settings.vector_db_type}")


def check_milvus():
    """用 pymilvus 测试 Milvus 连通性,不依赖 API Key。

    本地 Lite 模式(macOS/Linux)会临时建集合做读写;Windows 下若未配置
    MILVUS_URI,则提示改用 Docker 部署或 Zilliz Cloud。
    """
    import sys

    from pymilvus import MilvusClient

    from config.settings import settings

    if not settings.milvus_uri and sys.platform == "win32":
        print("  Milvus Lite 不支持 Windows;请配置 MILVUS_URI 使用 Docker 部署或 Zilliz Cloud。")
        print("  (跳过连通性测试)")
        return

    uri = settings.milvus_uri or settings.milvus_lite_path
    client = MilvusClient(uri)
    try:
        client.create_collection("_selfcheck", dimension=8)
        client.insert("_selfcheck", [{"id": 1, "vector": [0.1] * 8}])
        client.search("_selfcheck", data=[[0.1] * 8], limit=1)
        print(f"  Milvus 连接成功: {uri}")
        client.drop_collection("_selfcheck")
    except Exception as e:
        print(f"  Milvus 连接失败: {e}")


def main():
    print("== 1. 依赖导入 ==")
    check_imports()
    print("== 2. 配置 ==")
    check_config()
    print("== 3. 向量库连通性 ==")
    check_milvus()
    print("自检完成。")


if __name__ == "__main__":
    main()
