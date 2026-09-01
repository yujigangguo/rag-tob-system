"""数据库连接:SQLAlchemy engine、会话工厂、声明式基类。"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config.settings import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,       # 每次取连接前 ping 一下,自动剔除断开的连接
    pool_recycle=3600,        # 连接最大存活时间(秒),避免 MySQL 超时断开
    pool_size=20,             # 连接池大小(常驻连接数)
    max_overflow=10,          # 超出 pool_size 后最多可额外创建的连接数
    pool_timeout=30,          # 获取连接的超时时间(秒)
    echo=settings.db_echo,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def get_db():
    """FastAPI 依赖:提供一个数据库会话,请求结束后自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
