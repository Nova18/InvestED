from sqlalchemy.orm import Session

from app.db.models import Chunk, Document
from app.rag.embed import embed_texts

CHUNK_SIZE = 200  # words per chunk
CHUNK_OVERLAP = 40  # words shared between consecutive chunks


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start = end - overlap
    return chunks


def ingest_document(
    db: Session, title: str, source: str, text: str, url: str | None = None
) -> Document:
    document = Document(title=title, source=source, url=url)
    db.add(document)
    db.flush()  # assigns document.id without committing yet

    pieces = chunk_text(text)
    vectors = embed_texts(pieces)

    for index, (content, vector) in enumerate(zip(pieces, vectors)):
        db.add(Chunk(document_id=document.id, content=content, chunk_index=index, embedding=vector))

    db.commit()
    db.refresh(document)
    return document
