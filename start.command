#!/bin/zsh
cd "${0:A:h}"
url='http://127.0.0.1:8794'
if curl -fsS "$url/api/health" >/dev/null 2>&1; then
  open "$url"
  exit 0
fi
python3 server.py --port 8794 &
studio_pid=$!
trap 'kill "$studio_pid" 2>/dev/null' EXIT INT TERM
for attempt in {1..40}; do
  if curl -fsS "$url/api/health" >/dev/null 2>&1; then
    open "$url"
    break
  fi
  sleep 0.1
done
wait "$studio_pid"
