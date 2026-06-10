#!/usr/bin/env bash
# REST / curl — any language with an HTTP client works the same way.
set -euo pipefail
BASE="${SYNTHR_URL:-http://localhost:8000}"
KEY="${SYNTHR_KEY:-sk_proj_demo_secret}"

echo "== fillForm =="
curl -s -X POST "$BASE/v1/fillForm" -H "X-Project-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"fields":[{"name":"brand","type":"string"},{"name":"size","type":"number"}],
       "context":"Nike Air Max, size 10"}'
echo; echo "== summarize =="
curl -s -X POST "$BASE/v1/summarize" -H "X-Project-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"text":"Synthr is a self-hosted gateway that gives every project ready-made AI features behind one SDK.","max_words":12}'
echo; echo "== translate =="
curl -s -X POST "$BASE/v1/translate" -H "X-Project-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"text":"Good morning, how are you?","target_lang":"Spanish"}'
echo
