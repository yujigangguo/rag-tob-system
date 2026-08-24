"""对话接口:会话管理与流式问答。"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas.chat import (
    ChatMessageOut,
    ChatRequest,
    ChatSessionCreate,
    ChatSessionOut,
)
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["对话"])


@router.get("/sessions", response_model=list[ChatSessionOut], summary="会话列表")
def list_sessions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return chat_service.list_sessions(db, user.id)


@router.post("/sessions", response_model=ChatSessionOut, summary="新建会话")
def create_session(req: ChatSessionCreate, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    return chat_service.create_session(db, user.id, req.name)


@router.put("/sessions/{session_id}", response_model=ChatSessionOut, summary="重命名会话")
def rename_session(session_id: int, req: ChatSessionCreate,
                   user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return chat_service.rename_session(db, user.id, session_id, req.name)


@router.delete("/sessions/{session_id}", summary="删除会话")
def delete_session(session_id: int, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    chat_service.delete_session(db, user.id, session_id)
    return {"message": "删除成功"}


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageOut],
            summary="会话消息列表")
def list_messages(session_id: int, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    return chat_service.list_messages(db, user.id, session_id)


@router.post("/stream", summary="流式问答(SSE,所有登录用户可用)")
def stream_chat(req: ChatRequest, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """SSE 流式输出,每条数据格式: data: {"token": "..."} 结尾 data: {"citations": [...]} 与 data: [DONE]。"""
    prepared = chat_service.prepare_answer(db, user, req)
    citations = prepared.get("citations", [])

    def generate():
        try:
            for token in chat_service.stream_answer(
                prepared["messages"],
                prepared["session_id"],
                req,
                prepared.get("citations"),
                prepared.get("kb_ids"),
            ):
                yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
            # 引用映射:让前端把回答中的 [N] 渲染成可跳转到文档块的链接
            if citations:
                yield f"data: {json.dumps({'citations': citations}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:  # 生成过程中出错,以 SSE 形式返回
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
