# TODO(Phase 1): RAG pipeline lives here.
#
# You'll likely want:
#   - ingest.py    -> load knowledge base docs, chunk them
#   - embed.py     -> call embedding model, write vectors to pgvector
#   - retrieve.py  -> similarity search + reranking
#   - eval.py      -> scoring script against the 30 ground-truth Q&A pairs
