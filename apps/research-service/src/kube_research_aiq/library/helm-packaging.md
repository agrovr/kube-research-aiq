---
title: Packaging with Helm charts
url: https://helm.sh/docs/chart_best_practices/
topics: helm, chart, packaging, values, templates, configuration, deployment
---
Helm packages Kubernetes manifests as a chart of templates plus a values file, so one chart can describe a platform for a laptop, a free-tier node and a production cluster. Environment differences belong in layered values files rather than copies of manifests.

Chart best practices include consistent recommended labels, resource requests on every container, configurable security contexts and optional components behind enabled flags. Running helm lint and helm template in CI catches rendering errors before anything reaches a cluster.

Values that hold credentials should support referencing an existing Secret, so production installs never pass keys on the command line.
