from pydantic import BaseModel, Field


class AssistantChatRequest(BaseModel):
    question: str = Field(min_length=1)
    repository_id: str | None = None
    conversation_id: str | None = None


class AssistantSource(BaseModel):
    source_type: str
    source_id: str | None = None
    title: str


class AssistantChatResponse(BaseModel):
    answer: str
    sources: list[AssistantSource]
    confidence: float
    conversation_id: str
