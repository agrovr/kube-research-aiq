---
title: Scheduling GPUs on Kubernetes
url: https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/
topics: gpu, nvidia, scheduling, device plugin, inference, nodes, taints, self-hosted
---
Kubernetes schedules GPUs through device plugins, which advertise extended resources such as nvidia.com/gpu that Pods request in their resource limits. GPUs are requested as whole units by default and are not shared between containers unless a sharing mechanism such as time-slicing or Multi-Instance GPU is configured.

The NVIDIA GPU Operator automates the driver, container toolkit, device plugin and monitoring components needed on GPU nodes. Taints on GPU nodes keep ordinary workloads off expensive hardware, and tolerations plus node selectors place inference servers there.

A research platform does not need GPUs in the cluster when it calls hosted model endpoints; only self-hosted inference servers do. Separating the orchestration layer from the inference layer lets a team start on hosted APIs and move models in-house later without changing the agent code.
