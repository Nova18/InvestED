import json
from collections import defaultdict
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
OUT_OF_SCOPE_PATH = Path(__file__).resolve().parent.parent.parent / "eval" / "out_of_scope.json"
LOG_PATH = Path(__file__).resolve().parent.parent.parent / "eval" / "results_log.jsonl"


@dataclass
class EvalResult:
    question: str
    category: str
    hit: bool
    rank: int | None  # 1-indexed rank of first relevant chunk, None if not found
    top1_similarity: float | None  # similarity of the single best-matching chunk


def load_qa_pairs(path: Path = QA_PAIRS_PATH) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def load_out_of_scope(path: Path = OUT_OF_SCOPE_PATH) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def is_relevant(chunk_content: str, expected_keywords: list[str]) -> bool:
    content_lower = chunk_content.lower()
    return any(keyword.lower() in content_lower for keyword in expected_keywords)


def _rank_single_doc(retrieved: list[tuple[Chunk, float]], pair: dict) -> int | None:
    for i, (chunk, _) in enumerate(retrieved, start=1):
        doc_match = chunk.document.title == pair.get("expected_document")
        keyword_match = is_relevant(chunk.content, pair.get("expected_keywords", []))
        if doc_match or keyword_match:
            return i
    return None


def _rank_multi_hop(retrieved: list[tuple[Chunk, float]], pair: dict) -> int | None:
    expected_docs = set(pair["expected_documents"])
    seen_docs: set[str] = set()
    for i, (chunk, _) in enumerate(retrieved, start=1):
        seen_docs.add(chunk.document.title)
        if expected_docs.issubset(seen_docs):
            return i
    return None


def evaluate(db: Session, qa_pairs: list[dict], top_k: int = 10) -> list[EvalResult]:
    results = []
    for pair in qa_pairs:
        retrieved = retrieve(db, pair["question"], top_k=top_k)
        top1_similarity = retrieved[0][1] if retrieved else None

        if pair.get("category") == "multi_hop":
            rank = _rank_multi_hop(retrieved, pair)
        else:
            rank = _rank_single_doc(retrieved, pair)

        results.append(
            EvalResult(
                question=pair["question"],
                category=pair.get("category", "uncategorized"),
                hit=rank is not None,
                rank=rank,
                top1_similarity=top1_similarity,
            )
        )
    return results


def summarize(results: list[EvalResult]) -> dict:
    n = len(results)
    hit_rate = sum(r.hit for r in results) / n
    mrr = sum((1 / r.rank) if r.rank else 0 for r in results) / n
    top1 = sum(1 for r in results if r.rank == 1) / n
    top3 = sum(1 for r in results if r.rank is not None and r.rank <= 3) / n
    top5 = sum(1 for r in results if r.rank is not None and r.rank <= 5) / n
    return {"n": n, "hit_rate": hit_rate, "mrr": mrr, "top1": top1, "top3": top3, "top5": top5}


def summarize_by_category(results: list[EvalResult]) -> dict[str, dict]:
    by_category: dict[str, list[EvalResult]] = defaultdict(list)
    for r in results:
        by_category[r.category].append(r)
    return {category: summarize(rs) for category, rs in sorted(by_category.items())}


def out_of_scope_confidence(db: Session, out_of_scope_pairs: list[dict]) -> list[dict]:
    rows = []
    for pair in out_of_scope_pairs:
        retrieved = retrieve(db, pair["question"], top_k=1)
        similarity = retrieved[0][1] if retrieved else None
        rows.append({"question": pair["question"], "category": pair["category"], "top1_similarity": similarity})
    return rows


def log_run(db: Session, summary: dict, top_k: int, out_of_scope_avg: float | None = None) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_documents": db.scalar(select(func.count()).select_from(Document)),
        "n_chunks": db.scalar(select(func.count()).select_from(Chunk)),
        "n_questions": summary["n"],
        "top_k": top_k,
        "hit_rate": summary["hit_rate"],
        "mrr": summary["mrr"],
        "top1": summary["top1"],
        "top3": summary["top3"],
        "top5": summary["top5"],
        "out_of_scope_avg_similarity": out_of_scope_avg,
        "embedding_model": EMBEDDING_MODEL_NAME,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    from app.db.session import SessionLocal

    TOP_K = 10

    db = SessionLocal()
    try:
        results = evaluate(db, load_qa_pairs(), top_k=TOP_K)
        for r in results:
            status = f"HIT (rank {r.rank})" if r.hit else "MISS"
            print(f"[{r.category:<20}] [{status}] {r.question}")

        summary = summarize(results)
        print(
            f"\nOVERALL  n={summary['n']}  Hit Rate@{TOP_K}={summary['hit_rate']:.1%}  "
            f"MRR={summary['mrr']:.3f}  Top-1={summary['top1']:.1%}  "
            f"Top-3={summary['top3']:.1%}  Top-5={summary['top5']:.1%}"
        )

        print("\nBy category:")
        for category, cat_summary in summarize_by_category(results).items():
            print(
                f"  {category:<20} n={cat_summary['n']:<3} "
                f"hit_rate={cat_summary['hit_rate']:.1%}  mrr={cat_summary['mrr']:.3f}"
            )

        in_scope_avg_sim = sum(r.top1_similarity for r in results if r.top1_similarity) / len(results)

        oos_rows = out_of_scope_confidence(db, load_out_of_scope())
        oos_avg_sim = sum(r["top1_similarity"] for r in oos_rows) / len(oos_rows)
        print(f"\nOut-of-scope check ({len(oos_rows)} questions):")
        print(f"  In-scope avg top-1 similarity:     {in_scope_avg_sim:.3f}")
        print(f"  Out-of-scope avg top-1 similarity: {oos_avg_sim:.3f}")
        for row in oos_rows:
            print(f"  [{row['category']:<20}] sim={row['top1_similarity']:.3f}  {row['question']}")

        log_run(db, summary, top_k=TOP_K, out_of_scope_avg=oos_avg_sim)
        print(f"\nLogged to {LOG_PATH.relative_to(LOG_PATH.parents[2])}")
    finally:
        db.close()
