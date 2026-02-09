import httpx
import os
from src.env import env

async def llm_api_call(system_prompt: str, user_prompt: str) -> dict:
    """
    Make an API call to OpenAI's API with system and user prompts.
    
    Args:
        system_prompt: The system prompt to guide the model's behavior
        user_prompt: The user's input/query
        
    Returns:
        dict: The API response
    """
    api_key = env.OPENAI_API_KEY
    
    url = "https://api.openai.com/v1/responses"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Use proper role-based message structure
    data = {
        "model": "gpt-5.2",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise exception for bad status codes
        return response.json()
    