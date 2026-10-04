---
title: Controlling cost on Kubernetes AI platforms
url: https://kubernetes.io/docs/concepts/policy/resource-quotas/
topics: cost, budget, free tier, quotas, autoscaling, scale to zero, models, efficiency
---
The largest costs of an AI research platform are usually model inference and idle compute, not the orchestration layer itself. Routing simple questions to a shallow path with a small model, and reserving large models for deep synthesis, cuts inference spend substantially.

Scaling workers on queue depth, and to zero when idle, avoids paying for capacity that is waiting for work. Resource quotas and maximum replica counts put a hard ceiling on what a runaway workload can consume.

Very small clusters, such as a single free-tier virtual machine running k3s, can host the full platform for demos when the database and queue are tuned for low memory and the worker count is kept to one.
