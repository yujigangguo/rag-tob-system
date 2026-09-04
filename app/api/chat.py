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


@router.post("/regenerate", summary="重新生成最后一条回答")
def regenerate_last_answer(
    session_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除最后一条助手消息并重新生成。
    
    权限要求：登录用户
    """
    result = chat_service.regenerate_last_answer(db, user.id, session_id)
    return result


@router.delete("/messages/{message_id}", summary="删除消息")
def delete_message(
    message_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除指定消息及其后续消息。
    
    权限要求：登录用户
    """
    chat_service.delete_message(db, user.id, message_id)
    return {"message": "删除成功"}


@router.get("/sessions/{session_id}/export", summary="导出对话")
def export_session(
    session_id: int,
    format: str = "markdown",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """导出对话记录。
    
    支持格式:
    - markdown: 导出为 Markdown 文件
    - json: 导出为 JSON 文件
    
    权限要求：登录用户
    """
    from fastapi.responses import Response
    
    # 获取会话信息
    session = chat_service._get_session(db, user.id, session_id)
    messages = chat_service.list_messages(db, user.id, session_id)
    
    if format == "json":
        # JSON 格式导出
        export_data = {
            "session": {
                "id": session.id,
                "name": session.name,
                "created_at": str(session.created_at) if hasattr(session, 'created_at') else None,
            },
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": str(msg.created_at) if hasattr(msg, 'created_at') else None,
                }
                for msg in messages
            ]
        }
        content = json.dumps(export_data, ensure_ascii=False, indent=2)
        media_type = "application/json"
        filename = f"对话_{session.name}_{session_id}.json"
    else:
        # Markdown 格式导出
        lines = [
            f"# {session.name}",
            "",
            f"导出时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
        ]
        
        for msg in messages:
            role_name = "👤 用户" if msg.role == "user" else "🤖 助手"
            lines.append(f"## {role_name}")
            lines.append("")
            lines.append(msg.content)
            lines.append("")
            lines.append("---")
            lines.append("")
        
        content = "\n".join(lines)
        media_type = "text/markdown; charset=utf-8"
        filename = f"对话_{session.name}_{session_id}.md"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
