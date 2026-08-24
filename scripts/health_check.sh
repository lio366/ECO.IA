#!/usr/bin/env bash
# ECO-IA — Health check script
set -euo pipefail

API_URL="${1:-http://localhost:8000}"

resp=$(curl -sf "${API_URL}/health" 2>&1) || {
  echo "❌ Health check FAILED: ${API_URL}/health"
  exit 1
}

status=$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))")

if [ "$status" = "healthy" ]; then
  echo "✅ ECO-IA is healthy at ${API_URL}"
else
  echo "⚠️  ECO-IA status: ${status}"
  exit 1
fi
