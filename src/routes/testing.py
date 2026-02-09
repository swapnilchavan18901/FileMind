import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.llm.llm import llm_api_call
from src.llm.prompt.system_prompt import system_prompt
from src.db import prisma
# from src.llm.llm_run import run_chat
from src.vector.retrieve import retrieve_relevant_chunks

router = APIRouter(tags=["testing"])

class TestingRequest(BaseModel):
    question: str

@router.post("/testing/{bot_id}")
async def testing(
    bot_id: str,
    request: TestingRequest,
):
   try:
        bot = await prisma.bot.find_unique(
            where={"id": bot_id}
        )
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
            
        context = await retrieve_relevant_chunks(
            collection_name=bot_id,
            question=request.question,
        )
        print(f"contextishere111{context}")
        bot=bot.model_dump()
        answer = await llm_api_call(
            system_prompt=system_prompt,
            bot_prompt=bot['systemPrompt'],
            context=context,
            user_prompt=request.question,
        )
        return {
            "context": answer.get("choices")[0].get("message").get("content"),
        }
   except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
