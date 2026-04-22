from fastapi.testclient import TestClient

from kube_research_aiq import main
from kube_research_aiq.queue import ResearchQueue
from kube_research_aiq.researcher import ResearchRunner
from kube_research_aiq.settings import Settings
from kube_research_aiq.store import JobStore


def test_markdown_report_export(tmp_path, monkeypatch):
    settings = Settings(storage_path=tmp_path / "jobs.json")
    store = JobStore(settings)

    monkeypatch.setattr(main, "settings", settings)
    monkeypatch.setattr(main, "store", store)
    monkeypatch.setattr(main, "queue", ResearchQueue(settings))
    monkeypatch.setattr(main, "runner", ResearchRunner(settings, store))

    client = TestClient(main.app)
    created = client.post(
        "/v1/research",
        json={
            "query": "Compare Kubernetes orchestration options for AI research agents.",
            "depth": "shallow",
            "tenant": "test",
            "tags": ["export"],
        },
    )
    assert created.status_code == 202
    job_id = created.json()["job_id"]

    ran = client.post(f"/v1/research/{job_id}/run")
    assert ran.status_code == 200

    exported = client.get(f"/v1/research/{job_id}/report.md")
    assert exported.status_code == 200
    assert exported.headers["content-type"].startswith("text/markdown")
    assert "KubeResearch AIQ Report" in exported.text
    assert "Compare Kubernetes orchestration options" in exported.text
