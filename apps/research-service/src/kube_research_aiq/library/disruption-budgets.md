---
title: Disruptions and PodDisruptionBudgets
url: https://kubernetes.io/docs/concepts/workloads/pods/disruptions/
topics: availability, disruption, pdb, maintenance, upgrades, drain, reliability
---
Voluntary disruptions such as node drains during upgrades evict Pods, and a PodDisruptionBudget limits how many replicas of an application can be down at once. Setting minAvailable or maxUnavailable on the API keeps it serving during cluster maintenance.

Running at least two API replicas spread across nodes with topology spread constraints or anti-affinity removes single points of failure. Workers benefit from graceful shutdown handling, so an eviction finishes or requeues the current job instead of abandoning it.
