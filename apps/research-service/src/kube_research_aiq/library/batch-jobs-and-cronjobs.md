---
title: Jobs and CronJobs
url: https://kubernetes.io/docs/concepts/workloads/controllers/job/
topics: job, cronjob, batch, benchmark, evaluation, schedule, retries
---
A Kubernetes Job runs Pods until a specified number complete successfully, retrying failures up to a backoffLimit, and a CronJob creates Jobs on a schedule. Jobs suit finite work such as evaluations, migrations and report regeneration.

A scheduled benchmark that submits a fixed set of research questions and records latency and quality scores turns regressions in models or prompts into visible trends. Setting concurrencyPolicy to Forbid prevents a slow run from overlapping with the next one.

For continuous streams of user requests, a long-running worker Deployment reading from a queue is usually a better fit than a Job per request, because it avoids Pod start-up latency.
