---
title: Horizontal Pod Autoscaling
url: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
topics: autoscaling, hpa, cpu, scaling, replicas, metrics, cost
---
The HorizontalPodAutoscaler adjusts the replica count of a Deployment or StatefulSet to match observed load, most often average CPU utilisation relative to the Pods' resource requests. Autoscaling on CPU only works when containers declare CPU requests, because utilisation is measured as a percentage of the request.

CPU is a reasonable signal for a request-serving API, but it is a weak signal for research workers that spend most of their time waiting on model calls and web searches. A worker blocked on network I/O can show low CPU while a long queue builds up behind it.

The autoscaling/v2 API supports custom and external metrics, so a worker pool can scale on queue depth or on jobs in progress instead of CPU. Scale-down behaviour can be slowed with stabilization windows so that workers are not removed while a burst of deep research jobs is still draining.

Minimum replica counts keep the platform responsive to the first request, while maximum counts cap spend when a model endpoint is slow and work piles up.
