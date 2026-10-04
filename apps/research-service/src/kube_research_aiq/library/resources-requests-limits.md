---
title: Resource requests and limits
url: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
topics: resources, requests, limits, cpu, memory, scheduling, cost, qos
---
Resource requests tell the scheduler how much CPU and memory a container needs and decide where it is placed, while limits cap what it may consume at runtime. A container that exceeds its memory limit is killed with an out-of-memory error, while one that exceeds its CPU limit is throttled.

Requests also determine a Pod's quality-of-service class: Guaranteed when requests equal limits, Burstable when they differ, and BestEffort when none are set. Under node pressure, BestEffort and Burstable Pods are evicted first.

Agent workers that hold large prompts, retrieved documents and model responses in memory need realistic memory requests, measured under load rather than guessed. Small free-tier clusters benefit from conservative requests so that the API, worker, database and queue all fit on one node.
