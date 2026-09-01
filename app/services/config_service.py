"""系统配置服务。"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.models.system_config import SystemConfig

logger = get_logger(__name__)

# 默认配置
DEFAULT_CONFIGS = {
    "llm_model": {"value": "qwen-max", "description": "LLM 模型名称"},
    "llm_temperature": {"value": "0.7", "description": "LLM 温度参数"},
    "llm_max_tokens": {"value": "2048", "description": "LLM 最大 token 数"},
    "retrieval_top_k": {"value": "20", "description": "检索召回数量"},
    "final_top_k": {"value": "5", "description": "最终交给 LLM 的数量"},
    "captcha_enabled": {"value": "true", "description": "验证码开关"},
}


def init_default_configs(db: Session) -> None:
    """初始化默认配置（如果不存在）。"""
    for key, config in DEFAULT_CONFIGS.items():
        existing = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if not existing:
            db.add(SystemConfig(key=key, value=config["value"], description=config["description"]))
    db.commit()


def get_config(db: Session, key: str) -> Optional[str]:
    """获取配置值。"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return config.value if config else None


def get_all_configs(db: Session) -> list[dict]:
    """获取所有配置。"""
    configs = db.query(SystemConfig).order_by(SystemConfig.key).all()
    return [
        {
            "id": c.id,
            "key": c.key,
            "value": c.value,
            "description": c.description,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in configs
    ]


def update_config(db: Session, key: str, value: str) -> dict:
    """更新配置。"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if config:
        config.value = value
    else:
        config = SystemConfig(key=key, value=value)
        db.add(config)
    db.commit()
    db.refresh(config)
    logger.info("系统配置更新: %s = %s", key, value)
    return {
        "id": config.id,
        "key": config.key,
        "value": config.value,
        "description": config.description,
    }
