---
title: Network policies
url: https://kubernetes.io/docs/concepts/services-networking/network-policies/
topics: networkpolicy, security, network, isolation, egress, ingress, zero trust
---
NetworkPolicies control which Pods may talk to each other and to the outside world, and once any policy selects a Pod, traffic not explicitly allowed is denied. Policies are enforced by the cluster's network plugin, so a plugin with NetworkPolicy support such as Calico or Cilium is required.

A research platform can allow the dashboard to reach only the API, allow the API and workers to reach only Redis and PostgreSQL inside the cluster, and allow workers egress to model and search endpoints. Restricting egress limits the damage if an agent is manipulated into fetching or sending data it should not.

Policies select Pods by label, so consistent labels across a Helm chart are what make fine-grained rules practical. DNS egress to kube-dns must be allowed explicitly once egress rules are in place.
