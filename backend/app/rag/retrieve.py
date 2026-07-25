from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Chunk
from app.rag.embed import embed_text


def retrieve(db: Session, query: str, top_k: int = 5) -> list[tuple[Chunk, float]]:
    query_vector = embed_text(query)
    distance = Chunk.embedding.cosine_distance(query_vector)
    stmt = select(Chunk, distance).order_by(distance).limit(top_k)
    return [(chunk, 1 - dist) for chunk, dist in db.execute(stmt).all()]
