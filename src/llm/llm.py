from fastapi import HTTPException
from openai import AsyncOpenAI
from src.env import env

async def llm_api_call(system_prompt: str, bot_prompt: str, user_prompt: str, context: list[dict]) -> dict:
    """
    Make an API call to OpenAI's API with system and user prompts.
    
    Args:
        system_prompt: The system prompt to guide the model's behavior
        bot_prompt: Bot-specific instructions
        user_prompt: The user's input/query
        context: Document context for the query
        
    Returns:
        dict: The API response
    """
    client = AsyncOpenAI(api_key=env.OPENAI_API_KEY)
    
    # --- Build structured system prompt ---
    context_block = "\n\n".join(
        f"[Source: {chunk.get('file_name', 'unknown')}, Page: {chunk.get('page', 'N/A')}]\n{chunk.get('text', '')}"
        for chunk in context
    ) if context else "No relevant context found."

    final_prompt = (
        f"{system_prompt}\n\n"
        f"## Bot-Specific Instructions\n"
        f"Follow these instructions strictly when responding:\n{bot_prompt}\n\n"
        f"## Context (from uploaded documents)\n"
        f"Use ONLY the following excerpts to answer the user's question.\n\n"
        f"{context_block}"
    )

    try:
        # Use proper role-based message structure
        response = await client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": final_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Convert response to dict format
        data = response.model_dump()
        print(f"dataishere{data}")
        return data
    except Exception as e:
        print(f"errorishere{e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    