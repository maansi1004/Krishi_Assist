from pydantic import BaseModel, Field

class AssistantChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: str = "en"
    context_scheme_code: str | None = Field(default=None, max_length=80)
    history: list[dict] = Field(default_factory=list, max_length=8)

class AssistantChatResponse(BaseModel):
    reply: str
    intent: str
    schemes: list[dict] = []
    profile_used: bool = False
    eligibility: dict | None = None
