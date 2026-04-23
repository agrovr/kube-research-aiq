# Implementation Roadmap

## Milestone 1: Kubernetes-ready MVP

- FastAPI research API
- Worker process
- Redis queue and metadata store
- PostgreSQL durable job/report store
- Mock provider for deterministic local demos and CI
- NVIDIA-compatible chat completion provider
- Helm chart with secure workload defaults
- GitHub Actions CI and ArgoCD example
- React dashboard for research requests and report inspection
- kind demo scripts and local cluster deployment path
- Secure NVIDIA API key flow through Kubernetes Secrets
- Prometheus metrics and Grafana dashboard ConfigMap

## Milestone 2: AI-Q integration depth

- Add richer NVIDIA NIM model routing and fallback policies
- Import selected NVIDIA AI-Q workflow configs as examples
- Add Tavily and Serper tool adapters
- Add citation extraction and source ranking
- Add report export to Markdown and PDF
- Add report quality scoring and feedback capture

## Milestone 3: Production-grade Kubernetes

- OpenTelemetry tracing
- Prometheus dashboards and alerts
- KEDA queue-based worker autoscaling
- SealedSecrets or External Secrets Operator
- Ingress TLS with cert-manager

## Milestone 4: Project presentation

- Demo video and architecture diagram
- Sample reports committed under `examples/`
- One-command local Kubernetes install guide
- GitHub project board or issues showing engineering milestones
- A public write-up explaining tradeoffs and lessons learned
