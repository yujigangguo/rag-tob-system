"""FastAPI 应用入口。"""
from __future__ import annotations

import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  确保 ORM 模型注册
from app.api import admin, auth, chat, department, document, knowledge_base
from app.database import Base, engine
from app.logging_config import get_logger, setup_logging
from config.settings import settings

setup_logging()
logger = get_logger(__name__)

# 启动时自动建表(开发用;生产建议迁移到 Alembic)
Base.metadata.create_all(bind=engine)
logger.info("应用启动,已初始化日志与数据库表")

app = FastAPI(title=settings.app_name, version="1.0.0")

# 前后端分离,开发期允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件:记录方法、路径、状态码、耗时。"""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    # 健康检查跳过,避免刷屏
    if request.url.path != "/health":
        logger.info(
            "%s %s -> %d (%.2fms)",
            request.method, request.url.path, response.status_code, duration_ms,
        )
    return response

# 注册路由(统一加 /api 前缀)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(knowledge_base.router, prefix=settings.api_prefix)
app.include_router(document.documents_router, prefix=settings.api_prefix)
app.include_router(document.chunks_router, prefix=settings.api_prefix)
app.include_router(department.router, prefix=settings.api_prefix)
app.include_router(chat.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)


@app.get("/health", tags=["系统"])
def health():
    return {"status": "ok"}
