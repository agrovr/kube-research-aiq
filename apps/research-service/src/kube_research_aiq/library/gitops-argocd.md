---
title: GitOps delivery with Argo CD
url: https://argo-cd.readthedocs.io/en/stable/
topics: gitops, argocd, argo cd, deployment, delivery, helm, promotion, drift
---
Argo CD is a declarative GitOps controller that keeps a cluster in sync with manifests or Helm charts stored in Git. An Application resource names the repository, the path or chart, the values files and the target namespace.

Automated sync with self-heal reverts manual changes made directly in the cluster, so Git remains the single source of truth. Promotion between environments becomes a pull request that changes an image tag or a values file, which gives every release a review and an audit trail.

Argo CD shows drift, health and history for each Application, and rolling back means syncing to an earlier Git revision.
