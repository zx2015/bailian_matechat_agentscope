#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

export DASHSCOPE_API_KEY="${DASHSCOPE_API_KEY:-sk-test}"
export BAILIAN_APP_ID="${BAILIAN_APP_ID:-app-test}"

PYTHONPATH=src python -m uvicorn bailian_rag_demo.main:app \
    --host 127.0.0.1 --port 8000 &
SERVER_PID=$!
trap "kill $SERVER_PID 2>/dev/null || true" EXIT
sleep 3

echo "== /health =="
curl -fsS http://127.0.0.1:8000/health
echo

echo "== /process =="
curl -fsS -X POST http://127.0.0.1:8000/process \
    -H 'Content-Type: application/json' \
    -d '{"input":[{"role":"user","content":[{"type":"text","text":"hello"}]}]}'
echo