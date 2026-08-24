"""部门接口(部门数据由脚本/SQL 维护,这里仅提供列表供前端展示与建库选择)。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Department, User
from app.schemas.department import DepartmentOut

router = APIRouter(prefix="/departments", tags=["部门"])


@router.get("", response_model=list[DepartmentOut], summary="部门列表")
def list_departments(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(Department).order_by(Department.id)
    return list(db.scalars(stmt).all())
