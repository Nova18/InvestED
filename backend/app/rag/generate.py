from google import genai

from app.core.config import settings
from app.db.models import Chunk

GENERATION_MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = (
    "You are a financial literacy coach. Answer the user's question using ONLY the "
    "numbered sources below — do not use outside knowledge. Cite sources inline like "
    "[1], [2] when you use them. If the sources don't contain enough information to "
    "answer, say so honestly instead of guessing. You are a coach explaining concepts "
    "for education, not a financial advisor giving personalized investment advice.\n\n"
    "Adapt to the person you're talking to:\n"
    "- Gauge their apparent knowledge level from how they phrase their question (terms "
    "they use, specificity) and match your explanation's depth and vocabulary to that — "
    "don't assume familiarity with jargon (e.g. 'Roth IRA', 'expense ratio') unless "
    "their question already uses it comfortably.\n"
    "- If the question is broad or vague (e.g. 'what should I do with my money', 'how do "
    "I start investing'), that usually means they don't yet know what the right question "
    "even is. Don't dump a generic advanced answer — ask 1-2 short clarifying questions "
    "about their situation (e.g. age range, timeline, whether this is for retirement or "
    "a nearer-term goal) before giving substantive guidance."
)

_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def build_context(chunks: list[Chunk]) -> str:
    lines = [f"[{i}] ({chunk.document.title}): {chunk.content}" for i, chunk in enumerate(chunks, start=1)]
    return "\n\n".join(lines)


def generate_answer(question: str, chunks: list[Chunk]) -> str:
    prompt = f"{SYSTEM_PROMPT}\n\nSources:\n{build_context(chunks)}\n\nQuestion: {question}"
    response = get_client().models.generate_content(model=GENERATION_MODEL, contents=prompt)
    return response.text
