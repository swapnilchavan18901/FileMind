from fastapi import APIRouter, Depends, HTTPException
from src.db import prisma
from src.deps.auth import get_current_user
from src.utils.api_key import generate_api_key, hash_api_key

router = APIRouter(tags=["api-keys"])

@router.post("/bots/{bot_id}/api-keys")
async def create_api_key(
    bot_id: str,
    user = Depends(get_current_user)
):
    try:
        bot = await prisma.bot.find_unique(where={"id": bot_id},include={"apiKeys": True})
        print(f"botishere: {bot}")
        if not bot or bot.userId != user.id:
            raise HTTPException(status_code=404, detail="Bot not found")

        raw_key = generate_api_key()
        hashed_key = hash_api_key(raw_key)
        key_number = len(bot.apiKeys) + 1
        await prisma.apikey.create(
            data={
                "botId": bot_id,
                "keyHash": hashed_key,
                "name": f"ApiKey{key_number}",
            }
        )        # IMPORTANT: return raw key only once
        return {"apiKey": raw_key,"name": f"ApiKey{key_number}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bots/{bot_id}/api-keys")
async def list_api_keys(
    bot_id: str,
    user = Depends(get_current_user)
):
    try:
        bot = await prisma.bot.find_unique(where={"id": bot_id})

        if not bot or bot.userId != user.id:
            raise HTTPException(status_code=404, detail="Bot not found")

        keys = await prisma.apikey.find_many(
            where={"botId": bot_id},
        )

        return [{
            "id": k.id,
            "name": k.name,
            "isActive": k.isActive,
            "createdAt": k.createdAt,
            "lastUsedAt": k.lastUsedAt,
        } for k in keys]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api-keys/{api_key_id}")
async def revoke_api_key(
    api_key_id: str,
    user = Depends(get_current_user)
):
    try:
        key = await prisma.apikey.find_unique(where={"id": api_key_id})

        if not key:
            raise HTTPException(status_code=404, detail="API key not found")

        bot = await prisma.bot.find_unique(where={"id": key.botId})
        if bot.userId != user.id:
            raise HTTPException(status_code=403)

        await prisma.apikey.delete(where={"id": api_key_id})

        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
