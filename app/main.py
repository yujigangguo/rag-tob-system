"""FastAPI 应用入口。"""
from __future__ import annotations

import os
import time
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app import models  # noqa: F401  确保 ORM 模型注册
from app.api import admin, auth, chat, department, document, knowledge_base
from app.database import Base, engine
from app.logging_config import get_logger, setup_logging
from config.settings import settings

setup_logging()
logger = get_logger(__name__)

# 限频器:按 IP 限制
limiter = Limiter(key_func=get_remote_address)

# 自动建表:开发环境默认开启,生产环境建议使用 Alembic 迁移
# 设置环境变量 AUTO_CREATE_TABLES=false 可关闭自动建表
if os.getenv("AUTO_CREATE_TABLES", "true").lower() == "true":
    Base.metadata.create_all(bind=engine)
    logger.info("应用启动,已自动建表(生产环境建议使用 Alembic 迁移)")
else:
    logger.info("应用启动,自动建表已关闭(请确保已运行 alembic upgrade head)")

app = FastAPI(title=settings.app_name, version="1.0.0")

# 添加限频中间件
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 前后端分离,开发期允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 全局异常处理 ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """捕获所有未处理的异常,返回友好的错误信息。"""
    # 记录详细错误日志
    logger.error(
        "未处理异常: %s %s -> %s\n%s",
        request.method,
        request.url.path,
        str(exc),
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误，请稍后重试",
            "error_type": type(exc).__name__,
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """处理参数校验错误。"""
    logger.warning("参数错误: %s %s -> %s", request.method, request.url.path, str(exc))
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.exception_handler(ConnectionError)
async def connection_error_handler(request: Request, exc: ConnectionError):
    """处理数据库/外部服务连接错误。"""
    logger.error("连接错误: %s %s -> %s", request.method, request.url.path, str(exc))
    return JSONResponse(
        status_code=503,
        content={"detail": "服务暂时不可用，请稍后重试"},
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


@app.get("/health/deep", tags=["系统"], summary="深度健康检查")
def deep_health():
    """检查各组件连接状态。"""
    from sqlalchemy import text
    
    checks = {}
    
    # 检查 MySQL
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["mysql"] = {"status": "ok"}
    except Exception as e:
        checks["mysql"] = {"status": "error", "detail": str(e)}
    
    # 检查 Milvus
    try:
        from pymilvus import connections, utility
        connections.connect(
            alias="health_check",
            uri=settings.milvus_uri,
            token=settings.milvus_token or None,
        )
        # 简单操作验证连接
        utility.list_collections(using="health_check")
        connections.disconnect("health_check")
        checks["milvus"] = {"status": "ok"}
    except Exception as e:
        checks["milvus"] = {"status": "error", "detail": str(e)}
    
    # 检查 Redis (如果配置了)
    redis_url = os.getenv("REDIS_URL", "")
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url)
            r.ping()
            r.close()
            checks["redis"] = {"status": "ok"}
        except Exception as e:
            checks["redis"] = {"status": "error", "detail": str(e)}
    else:
        checks["redis"] = {"status": "not_configured"}
    
    # 总体状态
    all_ok = all(c["status"] in ("ok", "not_configured") for c in checks.values())
    
    return {
        "status": "ok" if all_ok else "degraded",
        "checks": checks,
    }
