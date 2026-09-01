"""审计日志服务。"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.models.audit_log import AuditLog

logger = get_logger(__name__)


def log_action(
    db: Session,
    user_id: Optional[int],
    username: str,
    action: str,
    target_type: str,
    target_id: Optional[int] = None,
    target_name: Optional[str] = None,
    detail: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> None:
    """记录审计日志。"""
    try:
        log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            detail=detail,
            ip_address=ip_address,
        )
        db.add(log)
        db.commit()
        logger.info("审计日志: %s %s %s/%s", username, action, target_type, target_id)
    except Exception as e:
        logger.error("审计日志记录失败: %s", e)
        db.rollback()


def get_audit_logs(
    db: Session,
    page: int = 1,
    page_size: int = 50,
    action: Optional[str] = None,
    username: Optional[str] = None,
) -> dict:
    """获取审计日志列表。"""
    from sqlalchemy import func, select
    
    query = select(AuditLog)
    
    if action:
        query = query.where(AuditLog.action == action)
    if username:
        query = query.where(AuditLog.username.ilike(f"%{username}%"))
    
    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query)
    
    query = query.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size)
    logs = db.scalars(query).all()
    
    return {
        "items": [
            {
                "id": log.id,
                "username": log.username,
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "target_name": log.target_name,
                "detail": log.detail,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
