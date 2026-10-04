import asyncio

import httpx

from kube_research_aiq.retrieval import Hit, KnowledgeLibrary, Retriever, stem, tokenize


def test_stemming_matches_related_forms():
    assert stem("security") == stem("secure")
    assert stem("observability") == stem("observe") == stem("observing")
    assert stem("scaling") == stem("scale") == stem("scaled")
    assert tokenize("The workers are scaling") == [stem("workers"), stem("scaling")]


def test_bundled_library_loads_every_brief_with_a_link():
    library = KnowledgeLibrary.bundled()
    assert len(library.documents) >= 20
    for doc in library.documents:
        assert doc.title and doc.passages
        assert doc.url and doc.url.startswith("https://")


def test_search_ranks_the_relevant_brief_first():
    library = KnowledgeLibrary.bundled()
    assert library.search("autoscale workers on redis queue length")[0].title.startswith(
        "Event-driven autoscaling")
    assert library.search("encrypt api keys and credentials")[0].key == "kb:secrets-management"
    assert library.search("")[0:1] == []
    assert library.search("the of and") == []


def test_search_is_deterministic():
    library = KnowledgeLibrary.bundled()
    assert library.search("network isolation egress") == library.search("network isolation egress")


class FakeWeb:
    name = "fake"

    def __init__(self, hits=None, error=None):
        self.hits, self.error = hits or [], error

    async def search(self, query, limit):
        if self.error:
            raise self.error
        return self.hits[:limit]


def test_retriever_interleaves_web_and_library(settings):
    web = [Hit(f"Web {i}", f"https://example.com/{i}", "content", "web", 1.0, f"web:{i}")
           for i in range(3)]
    retriever = Retriever(settings, web=FakeWeb(web))
    hits, warning = asyncio.run(retriever.search("kubernetes autoscaling", 4))
    assert warning is None
    assert [h.origin for h in hits] == ["web", "knowledge", "web", "knowledge"]
    assert retriever.origins == ["knowledge", "web:fake"]


def test_web_failure_falls_back_to_the_library(settings):
    retriever = Retriever(settings, web=FakeWeb(error=httpx.ConnectError("offline")))
    hits, warning = asyncio.run(retriever.search("kubernetes autoscaling", 3))
    assert hits and all(h.origin == "knowledge" for h in hits)
    assert warning and "Web search failed" in warning


def test_tavily_is_enabled_by_key(settings):
    keyed = settings.model_copy(update={"tavily_api_key": "tvly-test"})
    assert Retriever(keyed).origins == ["knowledge", "web:tavily"]
    assert Retriever(settings).origins == ["knowledge"]
