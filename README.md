# InvestED

AI Financial Coach — personalized financial literacy and investment guidance.
Educational coaching, **not financial advice**: the app learns who you are,
teaches you progressively, answers questions grounded in authoritative
documents (with citations), and eventually filters relevant market news.

## Stack

- **Frontend**: React (Vite + Tailwind)
- **Backend**: Python / FastAPI
- **Database**: PostgreSQL + pgvector
- **LLM**: Anthropic Claude (or OpenAI)
- **RAG orchestration**: LangChain / LlamaIndex (TBD)

## Getting started

### 1. Database

```bash
docker-compose up -d
```

Starts Postgres with the `pgvector` extension enabled on `localhost:5432`
(user `invested`, password `invested`, db `invested`).

### 2. Backend

```bash
cd backend
python3 -m venv .venv        # already created if you're reading this post-scaffold
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Runs on `http://localhost:8000`. Check `http://localhost:8000/api/health`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:5173`, proxies `/api/*` to the backend (see
`vite.config.js`).

## Project structure

```
backend/app/
  api/    # FastAPI routers (one module per resource)
  core/   # config/settings
  db/     # SQLAlchemy models + session
  rag/    # ingestion, embeddings, retrieval, eval harness
frontend/src/
db/init/  # SQL run once on first Postgres container start
```

## Roadmap

See project notes for the full phased plan:

1. RAG foundation — ingest knowledge base, pgvector storage, chat with citations, eval harness (30 Q&A pairs)
2. User profiling + confidence scoring/calibration
3. Ship to real users, collect thumbs up/down feedback
4. Curriculum engine — personalized lesson sequencing, quizzes, progress tracking
5. News integration — daily briefing filtered by user interests
6. Polish + writeup
