from fastapi import APIRouter, Depends, HTTPException
from src.db import prisma
from src.schemas.bots import BotCreateRequest, BotUpdateRequest
from src.deps.auth import get_current_user

router = APIRouter(prefix="/bots", tags=["bots"])

@router.post("")
async def create_bot(
    data: BotCreateRequest,
    user = Depends(get_current_user)
):
    print(f"userishere: {user}")

    bot = await prisma.bot.create(
        data={
            "name": data.name,
            "description": data.description,
            "systemPrompt": data.systemPrompt,
            "userId": user.id,
        }
    )

    return {
        "id": bot.id,
        "name": bot.name,
        "createdAt": bot.createdAt,
    }


@router.get("")
async def list_bots(user = Depends(get_current_user)):
    bots = await prisma.bot.find_many(
        where={"userId": user.id},
        order={"createdAt": "desc"},
    )

    return bots


@router.put("/{bot_id}")
async def update_bot(
    bot_id: str,
    data: BotUpdateRequest,
    user = Depends(get_current_user),
):
    bot = await prisma.bot.find_unique(where={"id": bot_id})

    if not bot or bot.userId != user.id:
        raise HTTPException(status_code=404, detail="Bot not found")

    updated = await prisma.bot.update(
        where={"id": bot_id},
        data=data.dict(exclude_unset=True),
    )

    return updated


@router.delete("/{bot_id}")
async def delete_bot(
    bot_id: str,
    user = Depends(get_current_user),
):
    bot = await prisma.bot.find_unique(where={"id": bot_id})

    if not bot or bot.userId != user.id:
        raise HTTPException(status_code=404, detail="Bot not found")

    await prisma.bot.delete(where={"id": bot_id})

    return {"success": True}
