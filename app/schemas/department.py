"""部门相关 schema。"""
from __future__ import annotations

from pydantic import BaseModel


class DepartmentOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
