import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Chunk, Document
from app.rag.embed import EMBEDDING_MODEL_NAME
from app.rag.ingest import CHUNK_OVERLAP, CHUNK_SIZE
from app.rag.retrieve import retrieve

QA_PAIRS_PATH = Path(__file__).resolve().parent.parent.parent / "eval" / "qa_pairs.json"
LOG_PATH = Path(__file__).resolve().parent.parent.parent / "eval" / "results_log.jsonl"


@dataclass
class EvalResult:
    question: str
    hit: bool
    rank: int | None  # 1-indexed rank of first relevant chunk, None if not found


def load_qa_pairs(path: Path = QA_PAIRS_PATH) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def is_relevant(chunk_content: str, expected_keywords: list[str]) -> bool:
    content_lower = chunk_content.lower()
    return any(keyword.lower() in content_lower for keyword in expected_keywords)


def evaluate(db: Session, qa_pairs: list[dict], top_k: int = 5) -> list[EvalResult]:
    results = []
    for pair in qa_pairs:
        chunks = retrieve(db, pair["question"], top_k=top_k)

        rank = None
        for i, chunk in enumerate(chunks, start=1):
            if is_relevant(chunk.content, pair["expected_keywords"]):
                rank = i
                break

        results.append(EvalResult(question=pair["question"], hit=rank is not None, rank=rank))
    return results


def summarize(results: list[EvalResult]) -> dict:
    n = len(results)
    hit_rate = sum(r.hit for r in results) / n
    mrr = sum((1 / r.rank) if r.rank else 0 for r in results) / n
    return {"n": n, "hit_rate": hit_rate, "mrr": mrr}


def log_run(db: Session, summary: dict, top_k: int) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_documents": db.scalar(select(func.count()).select_from(Document)),
        "n_chunks": db.scalar(select(func.count()).select_from(Chunk)),
        "n_questions": summary["n"],
        "top_k": top_k,
        "hit_rate": summary["hit_rate"],
        "mrr": summary["mrr"],
        "embedding_model": EMBEDDING_MODEL_NAME,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    from app.db.session import SessionLocal

    TOP_K = 5

    db = SessionLocal()
    try:
        results = evaluate(db, load_qa_pairs(), top_k=TOP_K)
        for r in results:
            status = f"HIT (rank {r.rank})" if r.hit else "MISS"
            print(f"[{status}] {r.question}")

        summary = summarize(results)
        print(f"\nn={summary['n']}  Hit Rate@{TOP_K}={summary['hit_rate']:.1%}  MRR={summary['mrr']:.3f}")

        log_run(db, summary, top_k=TOP_K)
        print(f"Logged to {LOG_PATH.relative_to(LOG_PATH.parents[2])}")
    finally:
        db.close()
