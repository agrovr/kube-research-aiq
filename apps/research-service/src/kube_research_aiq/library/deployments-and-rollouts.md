---
title: Deployments and rolling updates
url: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
topics: deployment, rollout, rolling update, rollback, stateless, replicas, api, worker
---
A Deployment manages a set of identical, stateless Pods through ReplicaSets and is the default way to run API servers and queue workers on Kubernetes. Because every replica is interchangeable, a Deployment can be scaled horizontally simply by changing its replica count.

The RollingUpdate strategy replaces Pods gradually, controlled by maxSurge and maxUnavailable, so a new version of a research API can ship without downtime. Readiness probes gate traffic during a rollout, which means a Pod only receives requests once it reports that its dependencies are reachable.

Every change to a Deployment's Pod template creates a new revision, and kubectl rollout undo returns to a previous revision when a release misbehaves. Keeping the API and the worker in separate Deployments lets each one roll out, scale and fail independently.

For agent platforms, the worker Deployment should set terminationGracePeriodSeconds long enough for an in-flight job to finish or checkpoint, and the worker should stop taking new jobs when it receives SIGTERM.
