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
    
    final_prompt = f"{system_prompt}\n\n this is the bot prompt follow these instructions strictly for chat purpose  {bot_prompt}\n\n this is context of the document for the user query and you should ans from this context only if the ans is not in this context then say i don't understand the question. Context: {context}"

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
    
    