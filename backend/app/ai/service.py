from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.ai.context import ContextBuilder
from app.ai.providers import get_embedding_provider, get_llm_provider
from app.ai.retrieval import HybridRetriever
from app.models.conversation import Conversation, ConversationMessage


class AssistantService:
    def chat(self, db: Session, question: str, repository_id: str | None = None, conversation_id: str | None = None) -> dict:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.repository_id == repository_id).first() if conversation_id else None
        if not conversation:
            conversation = Conversation(repository_id=repository_id)
            db.add(conversation)
            db.flush()
        history_rows = db.query(ConversationMessage).filter(ConversationMessage.conversation_id == conversation.id).order_by(ConversationMessage.created_at.desc()).limit(6).all()
        history = [{"role": row.role, "content": row.content} for row in reversed(history_rows)]
        evidence = HybridRetriever(get_embedding_provider()).search(db, question, repository_id)
        package = ContextBuilder().build(question, evidence, history)
        answer = get_llm_provider().answer(package["question"], package["evidence"], package["history"])
        db.add(ConversationMessage(conversation_id=conversation.id, role="user", content=question, source_refs=[]))
        refs = [{"source_type": item["source_type"], "source_id": item["source_id"], "title": item["title"]} for item in package["evidence"]]
        db.add(ConversationMessage(conversation_id=conversation.id, role="assistant", content=answer, source_refs=refs))
        conversation.updated_at = datetime.now(timezone.utc)
        db.commit()
        return {"answer": answer, "sources": refs, "confidence": round(sum(item.get("score", 0) for item in evidence[:3]) / max(len(evidence[:3]), 1), 3), "conversation_id": conversation.id}
