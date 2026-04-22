import asyncio

from kube_research_aiq.models import ResearchDepth, ResearchJob, ResearchRequest
from kube_research_aiq.researcher import ResearchRunner
from kube_research_aiq.settings import Settings
from kube_research_aiq.store import JobStore


def test_deep_research_mock_run(tmp_path):
    settings = Settings(provider="mock", storage_path=tmp_path / "jobs.json")
    store = JobStore(settings)
    job = store.create(
        ResearchJob(
            request=ResearchRequest(
                query="Compare Kubernetes deployment strategies for AI research agents.",
                depth=ResearchDepth.auto,
            )
        )
    )

    result = asyncio.run(ResearchRunner(settings, store).run(job.id))

    assert result.status == "succeeded"
    assert result.selected_depth == ResearchDepth.deep
    assert "Deep Research Report" in (result.report or "")
