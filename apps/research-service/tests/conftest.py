import fakeredis
import pytest

from kube_research_aiq.queue import ResearchQueue
from kube_research_aiq.researcher import ResearchRunner
from kube_research_aiq.settings import Settings
from kube_research_aiq.store import JobStore


@pytest.fixture
def settings(tmp_path):
    return Settings(provider="mock", storage_path=tmp_path / "jobs.json", redis_url=None,
                    database_url=None, tavily_api_key=None, nvidia_api_key=None)


@pytest.fixture
def store(settings):
    return JobStore(settings)


@pytest.fixture
def runner(settings, store):
    return ResearchRunner(settings, store)


@pytest.fixture
def redis_client():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def queue(settings, redis_client):
    return ResearchQueue(settings, client=redis_client)
