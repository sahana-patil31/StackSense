from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.ai.providers import ProviderError
from app.ai.service import AssistantService
from app.core.database import get_db
from app.core.security import require_engineer
from app.models.repository import Repository
from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse

router = APIRouter(prefix="/api/assistant", tags=["Assistant"])


@router.post("/chat", response_model=AssistantChatResponse)
def chat(payload: AssistantChatRequest, db: Session = Depends(get_db), _: object = Depends(require_engineer)) -> AssistantChatResponse:
    if payload.repository_id and not db.query(Repository).filter(Repository.id == payload.repository_id).first():
        raise HTTPException(status_code=404, detail=f"Repository '{payload.repository_id}' not found")
    try:
        return AssistantChatResponse.model_validate(AssistantService().chat(db, payload.question, payload.repository_id, payload.conversation_id))
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
