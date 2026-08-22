"""日志配置模块:统一的应用日志。

用法:
    # 应用启动时调用一次(app/main.py 已调用)
    setup_logging()

    # 各模块中获取 logger
    from app.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("用户注册成功: %s", username)
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.settings import settings

LOG_DIR = Path(settings.data_dir) / "logs"
LOG_FILE = LOG_DIR / "app.log"

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"

_configured = False


def setup_logging(level: int | str | None = None) -> None:
    """初始化日志(幂等,应用启动时调用一次)。

    输出到两处:控制台 + 文件(data/logs/app.log,按 10MB 轮转,保留 5 份)。
    """
    global _configured
    if _configured:
        return

    log_level = level or settings.log_level or "INFO"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(log_level.upper())

    formatter = logging.Formatter(_FORMAT, datefmt=_DATEFMT)

    # 控制台
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    # 文件(轮转)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # 降低第三方库的噪音
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """获取指定模块的 logger。"""
    return logging.getLogger(name)
