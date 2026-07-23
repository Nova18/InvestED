import argparse

from app.db.session import SessionLocal
from app.rag.ingest import chunk_text, ingest_document
from app.rag.loaders import load_url_text

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--title", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview extraction/chunking without writing to the DB"
    )
    args = parser.parse_args()

    text = load_url_text(args.url)
    print(f"Extracted {len(text)} characters from {args.url}")

    if args.dry_run:
        pieces = chunk_text(text)
        print(f"Would create {len(pieces)} chunks. First chunk preview:\n---")
        print(pieces[0][:1000])
        print("---")
        raise SystemExit(0)

    db = SessionLocal()
    try:
        document = ingest_document(
            db, title=args.title, source=args.source, text=text, url=args.url
        )
        print(f"Ingested document id={document.id}, {len(document.chunks)} chunks created.")
    finally:
        db.close()
