---
title: Pod security standards
url: https://kubernetes.io/docs/concepts/security/pod-security-standards/
topics: security, pod security, non root, read only filesystem, capabilities, hardening
---
The Pod Security Standards define three profiles: privileged, baseline and restricted. The restricted profile requires containers to run as a non-root user, disallow privilege escalation, drop all Linux capabilities and use a RuntimeDefault seccomp profile.

A read-only root filesystem prevents an exploited process from modifying its own binaries, and any scratch space can be supplied through an emptyDir volume. Applying these settings in a chart's default values makes secure configuration the path of least resistance.

Namespaces can enforce a profile with the pod-security.kubernetes.io/enforce label, rejecting Pods that do not comply.
