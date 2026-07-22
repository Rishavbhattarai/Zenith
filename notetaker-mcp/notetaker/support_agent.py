"""4.2: AI support agent grounded in the project's technical docs
(docs/runbooks/). Retrieval is plain bag-of-words cosine similarity --
the corpus is a handful of short docs, so TF-IDF/embeddings would be
premature. Only the answer-synthesis step needs an LLM, and that's
pluggable the same way notetaker.llm is, degrading gracefully to a mock
when no API key is configured.
"""

from __future__ import annotations

import math
import os
import re
import uuid
from collections import Counter
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

from notetaker.events import EVENT_LOG

DEFAULT_DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "runbooks"

_WORD_RE = re.compile(r"[a-z0-9]+")


class DocChunk(BaseModel):
    doc_title: str
    heading: str
    text: str


class SupportAnswer(BaseModel):
    answer: str
    sources: list[str]


def _tokenize(text: str) -> Counter:
    return Counter(_WORD_RE.findall(text.lower()))


def load_knowledge_base(docs_dir: Path = DEFAULT_DOCS_DIR) -> list[DocChunk]:
    chunks: list[DocChunk] = []
    for path in sorted(docs_dir.glob("*.md")):
        doc_title = path.stem.replace("-", " ").title()
        sections = re.split(r"^## (.+)$", path.read_text(), flags=re.MULTILINE)
        # sections[0] is the doc's leading H1/preamble; skip if empty of content
        preamble = sections[0].split("\n", 1)[-1].strip()
        if preamble:
            chunks.append(DocChunk(doc_title=doc_title, heading="Overview", text=preamble))
        for heading, body in zip(sections[1::2], sections[2::2]):
            chunks.append(DocChunk(doc_title=doc_title, heading=heading.strip(), text=body.strip()))
    return chunks


def _cosine_similarity(a: Counter, b: Counter) -> float:
    shared = set(a) & set(b)
    numerator = sum(a[w] * b[w] for w in shared)
    denom = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return numerator / denom if denom else 0.0


def retrieve(question: str, chunks: list[DocChunk], top_k: int = 3) -> list[DocChunk]:
    q_vec = _tokenize(question)
    scored = [(_cosine_similarity(q_vec, _tokenize(f"{c.heading} {c.text}")), c) for c in chunks]
    scored = [pair for pair in scored if pair[0] > 0]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [c for _, c in scored[:top_k]]


class AnswerGenerator(Protocol):
    def generate(self, question: str, chunks: list[DocChunk]) -> str: ...


class MockAnswerGenerator:
    def generate(self, question: str, chunks: list[DocChunk]) -> str:
        if not chunks:
            return "No relevant documentation found for this question."
        top = chunks[0]
        return f"[unformatted mock answer, top match from '{top.doc_title} → {top.heading}']\n{top.text}"


class GeminiAnswerGenerator:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate(self, question: str, chunks: list[DocChunk]) -> str:
        from google.genai import types

        if not chunks:
            return "No relevant documentation found for this question."

        context = "\n\n".join(f"### {c.doc_title} — {c.heading}\n{c.text}" for c in chunks)
        prompt = (
            f"Context from internal runbooks:\n\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer using only the context above, in a helpful, direct ops-support voice. "
            "If the context doesn't fully answer the question, say what's missing rather than guessing."
        )
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are Zenith's operations support agent. Answer strictly from the "
                    "provided runbook context -- never invent procedures or thresholds."
                )
            ),
        )
        return response.text


def get_answer_generator() -> AnswerGenerator:
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return GeminiAnswerGenerator(api_key=api_key)
    return MockAnswerGenerator()


_KNOWLEDGE_BASE = load_knowledge_base()


def ask_support_agent(question: str, generator: AnswerGenerator | None = None) -> SupportAnswer:
    note_id = f"support-{uuid.uuid4().hex[:8]}"
    chunks = retrieve(question, _KNOWLEDGE_BASE)
    EVENT_LOG.emit(note_id, "retrieval", f"Retrieved {len(chunks)} relevant doc chunk(s) for support query")

    answer = (generator or get_answer_generator()).generate(question, chunks)
    EVENT_LOG.emit(note_id, "answered", "Support agent produced an answer")

    sources = sorted({f"{c.doc_title} → {c.heading}" for c in chunks})
    return SupportAnswer(answer=answer, sources=sources)
