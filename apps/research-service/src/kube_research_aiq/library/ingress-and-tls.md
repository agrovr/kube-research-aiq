---
title: Ingress and TLS
url: https://kubernetes.io/docs/concepts/services-networking/ingress/
topics: ingress, tls, https, cert-manager, routing, public access, load balancer
---
An Ingress routes external HTTP and HTTPS traffic to Services by host and path, and it needs an ingress controller such as ingress-nginx or Traefik running in the cluster. A single Ingress can serve the dashboard at the root path and the research API under /v1 on the same host.

cert-manager issues and renews TLS certificates automatically, commonly from Let's Encrypt, and stores them in Secrets referenced by the Ingress. Lightweight distributions such as k3s ship Traefik as a default ingress controller, which makes small public demos straightforward.

Streaming endpoints such as server-sent events need proxy buffering disabled and generous read timeouts at the ingress so that updates reach the browser promptly.
