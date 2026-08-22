"""集中配置管理:数据库、大模型、向量库、认证等。

所有敏感信息和可变参数都通过环境变量(或 .env 文件)注入,
避免硬编码。字段名自动映射到同名环境变量(不区分大小写)。
"""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """全局配置单例。"""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---------- 应用 ----------
    app_name: str = "企业知识问答系统"
    api_prefix: str = "/api"
    secret_key: str = "change-me-in-production-please"  # JWT 签名密钥(生产务必修改)
    access_token_expire_minutes: int = 60 * 24          # token 有效期(分钟)
    log_level: str = "INFO"                             # 日志级别:DEBUG/INFO/WARNING/ERROR

    # ---------- MySQL 数据库 ----------
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "rag_user"
    db_password: str = "rag_pass123"
    db_name: str = "rag_db"
    db_echo: bool = False

    # ---------- 大模型(通义千问 qwen-max,OpenAI 兼容接口) ----------
    llm_api_key: str = ""
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen-max"
    llm_temperature: float = 0.7
    llm_top_p: float = 0.8
    llm_max_tokens: int = 2048

    # ---------- Embedding 模型(通义) ----------
    embedding_api_key: str = ""          # 通义 DashScope API Key
    embedding_model: str = "text-embedding-v3"
    embedding_dim: int = 1024

    # ---------- Rerank(可选) ----------
    rerank_api_key: str = ""
    rerank_model: str = "gte-rerank"

    # ---------- 历史对话 ----------
    default_history_rounds: int = 5      # 默认历史对话轮数

    # ---------- 图形验证码 ----------
    captcha_enabled: bool = True         # 验证码开关(测试/开发可关闭)
    captcha_expire_seconds: int = 300    # 验证码有效期(秒)
    captcha_length: int = 4

    # ---------- 检索参数 ----------
    retrieval_top_k: int = 20            # 混合检索召回数量
    final_top_k: int = 5                 # 交给 LLM 的数量

    # ---------- 向量库 Milvus ----------
    milvus_uri: str = "http://localhost:19530"
    milvus_token: str = ""
    milvus_collection_prefix: str = "kb_"  # 每个知识库一个 collection,前缀 kb_{kb_id}

    # ---------- 数据目录 ----------
    data_dir: str = str(BASE_DIR / "data")
    upload_dir: str = str(BASE_DIR / "data" / "uploads")      # 上传的原始文件
    raw_data_dir: str = str(BASE_DIR / "data" / "raw")
    processed_data_dir: str = str(BASE_DIR / "data" / "processed")

    @property
    def database_url(self) -> str:
        """SQLAlchemy 数据库连接串(MySQL + PyMySQL)。"""
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )


settings = Settings()
