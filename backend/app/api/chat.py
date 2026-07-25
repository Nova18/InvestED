from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.rag.calibration import PLATT_A, PLATT_B, apply_platt_scaling
from app.rag.generate import generate_answer
from app.rag.retrieve import retrieve

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


class Source(BaseModel):
    title: str
    source: str
    url: str | None


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    confidence: float


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    results = retrieve(db, request.question, top_k=5)
    chunks = [chunk for chunk, _ in results]
    answer = generate_answer(request.question, chunks)

    seen_ids: set[int] = set()
    sources = []
    for chunk, _ in results:
        doc = chunk.document
        if doc.id not in seen_ids:
            seen_ids.add(doc.id)
            sources.append(Source(title=doc.title, source=doc.source, url=doc.url))

    raw_similarity = results[0][1] if results else 0.0
    confidence = apply_platt_scaling(raw_similarity, PLATT_A, PLATT_B)
    return ChatResponse(answer=answer, sources=sources, confidence=confidence)
