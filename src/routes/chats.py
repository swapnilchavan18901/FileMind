from fastapi import APIRouter, Depends, HTTPException
from src.db import prisma
from src.deps.auth import get_current_user

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("/sessions/{bot_id}")
async def list_chat_sessions(
    bot_id: str,
    user=Depends(get_current_user),
):
    """List all chat sessions for a bot (owned by the current user)."""
    bot = await prisma.bot.find_unique(where={"id": bot_id})
    if not bot or bot.userId != user.id:
        raise HTTPException(status_code=404, detail="Bot not found")

    sessions = await prisma.chatsession.find_many(
        where={"botId": bot_id},
        include={
            "messages": {
                "order_by": {"createdAt": "desc"},
                "take": 1,
            }
        },
        order={"updatedAt": "desc"},
    )

    result = []
    for s in sessions:
        last_msg = s.messages[0] if s.messages else None
        # Skip sessions that have no user/assistant messages (only system prompt)
        if last_msg and last_msg.role == "system":
            continue
        result.append({
            "id": s.id,
            "botId": s.botId,
            "createdAt": s.createdAt.isoformat(),
            "updatedAt": s.updatedAt.isoformat(),
            "lastMessage": last_msg.content if last_msg else None,
            "lastRole": last_msg.role if last_msg else None,
        })

    return result


@router.get("/sessions/{session_id}/messages")
async def get_chat_messages(
    session_id: str,
    user=Depends(get_current_user),
):
    """Get all messages for a specific chat session."""
    session = await prisma.chatsession.find_unique(
        where={"id": session_id},
        include={"bot": True},
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.bot.userId != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    messages = await prisma.chatmessage.find_many(
        where={"sessionId": session_id},
        order={"createdAt": "asc"},
    )

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "createdAt": m.createdAt.isoformat(),
        }
        for m in messages
        if m.role != "system"  # Don't expose system prompts to frontend
    ]
