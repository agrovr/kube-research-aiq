#!/usr/bin/env bash
# Sends one deep dive to a running API and waits for it to surface with a cited report.
# Usage: scripts/smoke-test.sh [base-url] [timeout-seconds]
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
TIMEOUT="${2:-120}"

created=$(curl -fsS -X POST "$BASE_URL/v1/research" -H 'Content-Type: application/json' \
  -d '{"query":"Compare Kubernetes deployment strategies for AI research agents.","depth":"deep","tenant":"smoke-test","tags":["smoke"]}')
job_id=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["job_id"])' <<<"$created")
echo "Dive $job_id"

deadline=$((SECONDS + TIMEOUT))
while :; do
  job=$(curl -fsS "$BASE_URL/v1/research/$job_id")
  status=$(python3 -c 'import json,sys; j=json.load(sys.stdin); print(j["status"])' <<<"$job")
  python3 -c 'import json,sys; j=json.load(sys.stdin); print("  %-9s %-8s %3.0f%%" % (j["status"], j["stage"] or "", j["progress"] * 100))' <<<"$job"
  [[ "$status" == "queued" || "$status" == "running" ]] || break
  (( SECONDS < deadline )) || { echo "Timed out after ${TIMEOUT}s" >&2; exit 1; }
  sleep 2
done

python3 - "$job" <<'PY'
import json, sys
job = json.loads(sys.argv[1])
if job["status"] != "succeeded":
    sys.exit(f"Dive ended as {job['status']}: {job.get('error')}")
cited = {n for s in job["sections"] for n in s["source_ids"]}
assert job["sources"] and cited, "the report cites no sources"
assert cited <= {s["id"] for s in job["sources"]}, "a citation points at a missing source"
print(f"Surfaced: {job['title']} with {len(job['sources'])} sources across {len(job['sections'])} sections.")
PY
