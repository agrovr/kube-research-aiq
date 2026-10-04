---
title: Multi-tenancy and fairness
url: https://kubernetes.io/docs/concepts/security/multi-tenancy/
topics: multi tenancy, tenants, fairness, quotas, isolation, noisy neighbours, namespaces
---
Sharing one cluster between teams or customers saves cost and simplifies operations, but it raises questions of security, fairness and noisy neighbours. Namespaces, RBAC, ResourceQuotas and NetworkPolicies are the basic building blocks for separating tenants.

ResourceQuotas cap the total CPU, memory and object counts a namespace can consume, and LimitRanges set defaults for containers that do not declare requests. Application-level tenancy, such as a tenant field on every research job, needs its own limits so that one tenant cannot fill the shared queue.

Per-tenant queues or weighted scheduling keep a single heavy user from delaying everyone else's research.
