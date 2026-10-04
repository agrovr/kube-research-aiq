import json

import pytest
from fastapi.testclient import TestClient

from kube_research_aiq.main import create_app
from kube_research_aiq.models import JobStatus
from kube_research_aiq.queue import ResearchQueue

QUERY = {"query": "Compare Kubernetes orchestration options for AI research agents.",
         "depth": "auto", "tenant": "test", "tags": ["export"]}


@pytest.fixture
def client(settings, store, runner):
    # Background runs are off so each test controls when a job runs.
    manual = settings.model_copy(update={"enable_background_local_runs": False})
    app = create_app(manual, store, ResearchQueue(manual), runner, stream_interval=0.01)
    return TestClient(app)


def create(client, **overrides):
    response = client.post("/v1/research", json={**QUERY, **overrides})
    assert response.status_code == 202
    return response.json()["job_id"]


def test_create_run_and_export(client):
    job_id = create(client)
    assert client.get(f"/v1/research/{job_id}/report.md").status_code == 409
    ran = client.post(f"/v1/research/{job_id}/run").json()
    assert ran["status"] == "succeeded" and ran["selected_depth"] == "deep"
    assert ran["sources"][0]["id"] == 1 and ran["sections"]
    exported = client.get(f"/v1/research/{job_id}/report.md")
    assert exported.headers["content-type"].startswith("text/markdown")
    assert "attachment" in exported.headers["content-disposition"]
    assert "Kubernetes orchestration options for AI research agents" in exported.text
    assert f"job {job_id}" in exported.text


def test_background_runs_without_a_queue(settings, store, runner):
    client = TestClient(create_app(settings, store, ResearchQueue(settings), runner))
    response = client.post("/v1/research", json=QUERY)
    assert "background" in response.json()["message"]
    # TestClient runs background tasks before returning.
    assert client.get(f"/v1/research/{response.json()['job_id']}").json()["status"] == "succeeded"


def test_queue_dispatch(settings, store, runner, queue):
    client = TestClient(create_app(settings, store, queue, runner))
    response = client.post("/v1/research", json=QUERY)
    assert response.json()["message"] == "Queued for a worker."
    assert queue.depth() == (1, 0)


def test_list_and_filter(client):
    first, second = create(client), create(client, query="What is KEDA?")
    client.post(f"/v1/research/{first}/run")
    jobs = client.get("/v1/research").json()["jobs"]
    assert [j["id"] for j in jobs] == [second, first]  # newest first
    queued = client.get("/v1/research", params={"status": "queued"}).json()["jobs"]
    assert [j["id"] for j in queued] == [second]


def test_cancel_and_retry(client):
    job_id = create(client)
    cancelled = client.post(f"/v1/research/{job_id}/cancel").json()
    assert cancelled["status"] == "cancelled"
    assert client.post(f"/v1/research/{job_id}/cancel").status_code == 409
    retried = client.post(f"/v1/research/{job_id}/retry")
    assert retried.json()["status"] == "queued"
    assert client.post(f"/v1/research/{job_id}/run").json()["status"] == "succeeded"
    assert client.post(f"/v1/research/{job_id}/retry").status_code == 409


def test_missing_jobs_are_404(client):
    for path in ["", "/report.md", "/events"]:
        assert client.get(f"/v1/research/nope{path}").status_code == 404
    for action in ["run", "cancel", "retry"]:
        assert client.post(f"/v1/research/nope/{action}").status_code == 404


def test_validation(client):
    assert client.post("/v1/research", json={"query": "hi"}).status_code == 422
    assert client.post("/v1/research", json={**QUERY, "depth": "abyssal"}).status_code == 422


def test_event_stream_ends_when_the_job_finishes(client):
    job_id = create(client)
    client.post(f"/v1/research/{job_id}/run")
    with client.stream("GET", f"/v1/research/{job_id}/events") as response:
        assert response.headers["content-type"].startswith("text/event-stream")
        text = "".join(response.iter_text())
    events = [block for block in text.split("\n\n") if block.startswith("event:")]
    assert events[0].startswith("event: job")
    assert json.loads(events[0].split("data: ", 1)[1])["status"] == "succeeded"
    assert events[-1].startswith("event: done")


def test_meta_library_health_and_metrics(client):
    meta = client.get("/v1/meta").json()
    assert meta["writer"] == "offline" and meta["retrieval"] == ["knowledge"]
    assert meta["store"] == "file" and meta["library_documents"] >= 20
    library = client.get("/v1/library").json()
    assert len(library) == meta["library_documents"] and library[0]["url"].startswith("https://")
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").json()["status"] == "ready"
    create(client)
    metrics = client.get("/metrics").text
    assert 'krai_jobs_by_status{status="queued"} 1.0' in metrics
    assert "krai_jobs_created_total" in metrics


def test_statuses_are_complete():
    assert {s.value for s in JobStatus} == {"queued", "running", "succeeded", "failed",
                                            "cancelled"}
