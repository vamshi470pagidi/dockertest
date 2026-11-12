#!/usr/bin/env bash
# End-to-end smoke test against the running stack
set -euo pipefail
BASE=${1:-http://localhost:8080}

curl -fsS "$BASE/health"; echo
ID=$(curl -fsS -X POST "$BASE/tasks" -H 'Content-Type: application/json' \
      -d '{"title":"learn docker"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
echo "created task $ID"
curl -fsS "$BASE/tasks" | grep -q '"source":"db"'    && echo "1st read: db OK"
curl -fsS "$BASE/tasks" | grep -q '"source":"cache"' && echo "2nd read: cache OK"
curl -fsS -X PATCH "$BASE/tasks/$ID/done" >/dev/null && echo "marked done OK"
echo "SMOKE TEST PASSED"
