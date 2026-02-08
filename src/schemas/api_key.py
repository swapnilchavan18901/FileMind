from pydantic import BaseModel

class ApiKeyCreateResponse(BaseModel):
    apiKey: str   # returned ONLY once
