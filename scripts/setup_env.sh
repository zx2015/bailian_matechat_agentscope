#!/usr/bin/env bash
# Print the environment variable names this app expects.
# Use as a checklist; set real values in your shell before running.
set -euo pipefail
cat <<'EOF'
Required for upload (runtime-fc-deploy):
  ALIBABA_CLOUD_ACCESS_KEY_ID
  ALIBABA_CLOUD_ACCESS_KEY_SECRET
  MODELSTUDIO_WORKSPACE_ID   (optional)

Required at app runtime:
  DASHSCOPE_API_KEY
  BAILIAN_APP_ID

Optional:
  BAILIAN_RAG_TOP_K   (default 5)
  RAG_TIMEOUT_SEC     (default 5.0)
  LOG_LEVEL           (default INFO)
EOF
