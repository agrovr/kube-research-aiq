---
title: Event-driven autoscaling with KEDA
url: https://keda.sh/docs/latest/scalers/redis-lists/
topics: keda, autoscaling, queue, redis, scale to zero, worker, event driven, cost
---
KEDA is a Kubernetes event-driven autoscaler that scales workloads on the length of external queues and streams rather than on CPU. Its Redis Lists scaler watches a list key and targets an average number of pending items per replica, set with the listLength field.

For asynchronous research platforms, queue depth is the most direct measure of demand: ten waiting deep-research jobs mean more workers are needed regardless of CPU. KEDA creates and manages an HPA behind the scenes, so it composes with existing Kubernetes scaling machinery.

KEDA can scale a Deployment to zero replicas when the queue is empty and back up when work arrives, which suits bursty research workloads and keeps idle cost low. An activation threshold controls when scaling from zero begins.

Credentials for the queue are supplied through a TriggerAuthentication resource that reads from a Kubernetes Secret, so the scaler never needs passwords in plain manifests.
