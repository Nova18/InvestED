from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Chunk
from app.rag.embed import embed_text


def retrieve(db: Session, query: str, top_k: int = 5) -> list[Chunk]:
    query_vector = embed_text(query)
    stmt = select(Chunk).order_by(Chunk.embedding.cosine_distance(query_vector)).limit(top_k)
    return list(db.scalars(stmt))
