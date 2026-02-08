from pydantic import BaseModel, Field

class BotCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None
    systemPrompt: str | None = None


class BotUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    systemPrompt: str | None = None
    isActive: bool | None = None
