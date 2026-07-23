import re

import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup

_PRINT_ARTIFACT = re.compile(
    r"\S+\.qxd\s+\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}\s*[AP]M\s+Page\s+\S+"
)


def load_pdf_text(path: str) -> str:
    doc = fitz.open(path)
    pages = [page.get_text() for page in doc]
    text = "\n".join(pages)
    return _clean(text)


def load_url_text(url: str) -> str:
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    return _clean(text)


def _clean(text: str) -> str:
    text = _PRINT_ARTIFACT.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
