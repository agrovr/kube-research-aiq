from fastapi.testclient import TestClient

from kube_research_aiq.main import app


def test_markdown_report_export():
    client = TestClient(app)
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
