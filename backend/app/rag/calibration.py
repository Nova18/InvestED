import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.rag.eval import is_relevant, load_out_of_scope, load_qa_pairs
from app.rag.retrieve import retrieve

N_BINS = 5
K_FOLDS = 5
LOG_PATH = Path(__file__).resolve().parent.parent.parent / "eval" / "calibration_log.jsonl"

# Fitted by running `python -m app.rag.calibration` on the full eval set (n=122, 2026-07-24).
# Refit and update these if the knowledge base grows or changes significantly.
PLATT_A = 11.855
PLATT_B = -5.829


def collect_calibration_data(db: Session, qa_pairs: list[dict], out_of_scope_pairs: list[dict]) -> list[tuple[float, bool]]:
    points: list[tuple[float, bool]] = []

    for pair in qa_pairs:
        if pair.get("category") == "multi_hop":
            continue
        retrieved = retrieve(db, pair["question"], top_k=1)
        if not retrieved:
            continue
        chunk, similarity = retrieved[0]
        doc_match = chunk.document.title == pair.get("expected_document")
        keyword_match = is_relevant(chunk.content, pair.get("expected_keywords", []))
        points.append((similarity, doc_match or keyword_match))

    for pair in out_of_scope_pairs:
        retrieved = retrieve(db, pair["question"], top_k=1)
        if not retrieved:
            continue
        _, similarity = retrieved[0]
        points.append((similarity, False))

    return points


def bucket_calibration(points: list[tuple[float, bool]], n_bins: int = N_BINS) -> list[dict]:
    if not points:
        return []
    lo = min(c for c, _ in points)
    hi = max(c for c, _ in points)
    width = (hi - lo) / n_bins or 1e-9

    bins: list[list[tuple[float, bool]]] = [[] for _ in range(n_bins)]
    for confidence, correct in points:
        idx = min(int((confidence - lo) / width), n_bins - 1)
        bins[idx].append((confidence, correct))

    rows = []
    for i, b in enumerate(bins):
        if not b:
            continue
        avg_confidence = sum(c for c, _ in b) / len(b)
        accuracy = sum(1 for _, correct in b if correct) / len(b)
        rows.append(
            {
                "bin_low": lo + i * width,
                "bin_high": lo + (i + 1) * width,
                "n": len(b),
                "avg_confidence": avg_confidence,
                "accuracy": accuracy,
                "gap": abs(avg_confidence - accuracy),
            }
        )
    return rows


def expected_calibration_error(points: list[tuple[float, bool]], n_bins: int = N_BINS) -> float:
    rows = bucket_calibration(points, n_bins)
    total = sum(r["n"] for r in rows)
    return sum((r["n"] / total) * r["gap"] for r in rows) if total else 0.0


def sigmoid(z: float) -> float:
    z = max(min(z, 500), -500)  # clamp to avoid math.exp overflow
    return 1 / (1 + math.exp(-z))


def fit_platt_scaling(
    points: list[tuple[float, bool]], lr: float = 0.5, epochs: int = 3000
) -> tuple[float, float]:
    """Fit calibrated = sigmoid(A * similarity + B) via gradient descent on binary cross-entropy."""
    a, b = 0.0, 0.0
    n = len(points)
    for _ in range(epochs):
        grad_a = 0.0
        grad_b = 0.0
        for similarity, correct in points:
            y = 1.0 if correct else 0.0
            p = sigmoid(a * similarity + b)
            grad_a += (p - y) * similarity
            grad_b += p - y
        a -= lr * (grad_a / n)
        b -= lr * (grad_b / n)
    return a, b


def apply_platt_scaling(similarity: float, a: float, b: float) -> float:
    return sigmoid(a * similarity + b)


def cross_validated_calibration(
    points: list[tuple[float, bool]], k: int = K_FOLDS, seed: int = 42
) -> list[tuple[float, bool]]:
    """Return (calibrated_confidence, correct) pairs, each predicted by a model that never saw that point."""
    shuffled = points[:]
    random.Random(seed).shuffle(shuffled)
    folds = [shuffled[i::k] for i in range(k)]

    held_out: list[tuple[float, bool]] = []
    for i in range(k):
        test_fold = folds[i]
        train_fold = [p for j, fold in enumerate(folds) if j != i for p in fold]
        a, b = fit_platt_scaling(train_fold)
        for similarity, correct in test_fold:
            held_out.append((apply_platt_scaling(similarity, a, b), correct))
    return held_out


def log_run(n_points: int, raw_ece: float, cv_ece: float, a: float, b: float) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_points": n_points,
        "n_bins": N_BINS,
        "k_folds": K_FOLDS,
        "raw_ece": raw_ece,
        "cv_ece": cv_ece,
        "platt_a": a,
        "platt_b": b,
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")


def _print_table(rows: list[dict]) -> None:
    print(f"{'Confidence range':<20}{'n':<6}{'Avg confidence':<18}{'Accuracy':<12}{'Gap':<8}")
    for r in rows:
        bin_range = f"{r['bin_low']:.2f}-{r['bin_high']:.2f}"
        print(
            f"{bin_range:<20}{r['n']:<6}{r['avg_confidence']:<18.3f}"
            f"{r['accuracy']:<12.3f}{r['gap']:<8.3f}"
        )


if __name__ == "__main__":
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        points = collect_calibration_data(db, load_qa_pairs(), load_out_of_scope())

        print(f"=== RAW (uncalibrated) similarity, n={len(points)} ===\n")
        raw_rows = bucket_calibration(points)
        _print_table(raw_rows)
        raw_ece = expected_calibration_error(points)
        print(f"\nRaw ECE: {raw_ece:.3f}")

        print(f"\n=== {K_FOLDS}-fold cross-validated Platt scaling ===\n")
        cv_points = cross_validated_calibration(points)
        cv_rows = bucket_calibration(cv_points)
        _print_table(cv_rows)
        cv_ece = expected_calibration_error(cv_points)
        print(f"\nCross-validated ECE: {cv_ece:.3f}  (raw was {raw_ece:.3f})")
        print(f"(n={len(points)} — small-sample estimate; would benefit from more data, especially in the low/mid-confidence range, for tighter bins)")

        final_a, final_b = fit_platt_scaling(points)
        print(f"\nFinal Platt scaling params (fit on all data, for production use): A={final_a:.3f}, B={final_b:.3f}")

        log_run(len(points), raw_ece, cv_ece, final_a, final_b)
        print(f"Logged to {LOG_PATH.relative_to(LOG_PATH.parents[2])}")
    finally:
        db.close()
