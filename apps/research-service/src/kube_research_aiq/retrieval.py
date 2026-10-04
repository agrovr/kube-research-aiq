"""Source retrieval: a bundled knowledge library ranked with BM25, plus optional web search."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from importlib import resources
from typing import Protocol

import httpx

from kube_research_aiq.settings import Settings

STOPWORDS = frozenset(
    """a about above after again against all am an and any are as at be because been before being
    below between both but by can could did do does doing down during each few for from further had
    has have having how i if in into is it its itself just me more most my no nor not now of off on
    once only or other our out over own same should so some such than that the their them then there
    these they this those through to too under until up very was we were what when where which while
    who whom why will with would you your use using used recommend compare evaluate explain best way
    ways need needs""".split()
)

TOKEN = re.compile(r"[a-z0-9]+")


SUFFIXES = ("ations", "ation", "ability", "ities", "ity", "ments", "ment", "ness", "ings", "ing",
            "ies", "ers", "er", "ed", "es", "ly", "s", "e")


def stem(word: str) -> str:
    """A deliberately small stemmer, enough to match secure/security or scale/scaling/scaled."""
    for suffix in SUFFIXES:
        if len(word) - len(suffix) >= 4 and word.endswith(suffix):
            word = word[: -len(suffix)] + ("y" if suffix in ("ies", "ities") else "")
            break
    if len(word) > 4 and word.endswith("e"):
        word = word[:-1]
    return word


def tokenize(text: str) -> list[str]:
    return [stem(t) for t in TOKEN.findall(text.lower()) if t not in STOPWORDS and len(t) > 1]


@dataclass(frozen=True)
class Passage:
    doc_slug: str
    title: str
    url: str | None
    text: str
    topics: tuple[str, ...]


@dataclass(frozen=True)
class Hit:
    title: str
    url: str | None
    text: str
    origin: str
    score: float
    key: str  # identifies the underlying document, for de-duplication


@dataclass
class Document:
    slug: str
    title: str
    url: str | None
    topics: tuple[str, ...]
    passages: list[str] = field(default_factory=list)


def parse_document(slug: str, raw: str) -> Document:
    meta: dict[str, str] = {}
    body = raw
    if raw.startswith("---"):
        _, header, body = raw.split("---", 2)
        for line in header.strip().splitlines():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    topics = tuple(t.strip() for t in meta.get("topics", "").split(",") if t.strip())
    passages = [p.strip().replace("\n", " ") for p in body.strip().split("\n\n") if p.strip()]
    return Document(slug, meta.get("title", slug), meta.get("url") or None, topics, passages)


class KnowledgeLibrary:
    """BM25 over the paragraphs of the bundled briefs. No embeddings, no network, deterministic."""

    k1 = 1.4
    b = 0.75

    def __init__(self, documents: list[Document]):
        self.documents = documents
        self.passages: list[Passage] = []
        for doc in documents:
            for text in doc.passages:
                self.passages.append(Passage(doc.slug, doc.title, doc.url, text, doc.topics))
        # Title and topics are folded into every passage so short paragraphs match their theme.
        self._tokens = [
            tokenize(f"{p.title} {' '.join(p.topics)} {p.text}") for p in self.passages
        ]
        self._lengths = [len(t) for t in self._tokens]
        self._avg = sum(self._lengths) / max(len(self._lengths), 1)
        self._tf = [Counter(t) for t in self._tokens]
        df: Counter[str] = Counter()
        for tokens in self._tokens:
            df.update(set(tokens))
        n = len(self.passages)
        self._idf = {term: math.log(1 + (n - f + 0.5) / (f + 0.5)) for term, f in df.items()}

    @classmethod
    def bundled(cls) -> KnowledgeLibrary:
        return _bundled_library()

    def search(self, query: str, limit: int = 5) -> list[Hit]:
        terms = tokenize(query)
        if not terms:
            return []
        scored: list[tuple[float, int]] = []
        for index, tf in enumerate(self._tf):
            score = 0.0
            for term in terms:
                freq = tf.get(term)
                if not freq:
                    continue
                norm = freq + self.k1 * (1 - self.b + self.b * self._lengths[index] / self._avg)
                score += self._idf[term] * freq * (self.k1 + 1) / norm
            if score > 0:
                scored.append((score, index))
        scored.sort(key=lambda item: (-item[0], item[1]))
        hits: list[Hit] = []
        for score, index in scored[:limit]:
            p = self.passages[index]
            hits.append(
                Hit(p.title, p.url, p.text, "knowledge", round(score, 3), f"kb:{p.doc_slug}")
            )
        return hits


@lru_cache
def _bundled_library() -> KnowledgeLibrary:
    folder = resources.files("kube_research_aiq") / "library"
    documents = [
        parse_document(entry.name.removesuffix(".md"), entry.read_text(encoding="utf-8"))
        for entry in sorted(folder.iterdir(), key=lambda e: e.name)
        if entry.name.endswith(".md")
    ]
    return KnowledgeLibrary(documents)


class WebSearch(Protocol):
    name: str

    async def search(self, query: str, limit: int) -> list[Hit]: ...


class TavilySearch:
    name = "tavily"
    endpoint = "https://api.tavily.com/search"

    def __init__(self, api_key: str, timeout: float = 20.0):
        self.api_key = api_key
        self.timeout = timeout

    async def search(self, query: str, limit: int) -> list[Hit]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.endpoint,
                json={"query": query[:400], "max_results": limit, "search_depth": "basic"},
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
            results = response.json().get("results", [])
        return [
            Hit(
                title=r.get("title") or r.get("url", "Untitled"),
                url=r.get("url"),
                text=(r.get("content") or "").strip(),
                origin="web",
                score=float(r.get("score") or 0.0),
                key=f"web:{r.get('url')}",
            )
            for r in results
            if r.get("content")
        ]


class Retriever:
    """Searches the library and, when configured, the web; merges the two."""

    def __init__(self, settings: Settings, library: KnowledgeLibrary | None = None,
                 web: WebSearch | None = None):
        self.settings = settings
        self.library = library or KnowledgeLibrary.bundled()
        self.web = web
        if self.web is None and settings.tavily_api_key:
            self.web = TavilySearch(settings.tavily_api_key, settings.request_timeout_seconds)

    @property
    def origins(self) -> list[str]:
        return ["knowledge"] + ([f"web:{self.web.name}"] if self.web else [])

    async def search(self, query: str, limit: int) -> tuple[list[Hit], str | None]:
        """Returns hits and, if web search failed, a warning to record on the job."""
        hits = self.library.search(query, limit)
        warning = None
        if self.web:
            try:
                web_hits = await self.web.search(query, limit)
            except (httpx.HTTPError, ValueError) as exc:
                warning = f"Web search failed, continuing with the library: {exc}"
            else:
                # Interleave so both origins are represented near the top.
                merged: list[Hit] = []
                for pair in zip(web_hits, hits, strict=False):
                    merged.extend(pair)
                longer = web_hits if len(web_hits) > len(hits) else hits
                merged.extend(longer[min(len(web_hits), len(hits)):])
                hits = merged[:limit]
        return hits, warning
