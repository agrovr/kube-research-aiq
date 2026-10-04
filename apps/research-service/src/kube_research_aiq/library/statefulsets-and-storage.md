---
title: StatefulSets and persistent storage
url: https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/
topics: statefulset, storage, persistent volume, postgres, redis, database, state
---
A StatefulSet gives each Pod a stable network identity and its own PersistentVolumeClaim, which is what databases such as PostgreSQL and Redis need to survive restarts. Pods in a StatefulSet are created and terminated in order, and each keeps the same volume when it is rescheduled.

Running a single-replica PostgreSQL or Redis StatefulSet inside the cluster is a good fit for demos, development and small installations. Production platforms usually move these to a managed database service, which handles backups, failover, upgrades and point-in-time recovery.

Volume claim templates request storage from a StorageClass, so the same chart can run on a laptop with a local-path provisioner and on a cloud cluster with network block storage. Persistent volumes are not deleted when a StatefulSet is removed, which protects data from accidental uninstalls.

Research platforms should treat the job store as the source of truth: reports, sources and timelines live in the database, while the queue holds only job identifiers that can be rebuilt.
