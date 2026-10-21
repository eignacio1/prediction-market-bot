#!/bin/bash
# PMBot Visual Dashboard — double-click to open.
# The box builds the page live from origin/main (scripts/web_dashboard.py, /visual), so it is always current.
# This opens the SSH tunnel (same one as the Live Terminal) and the page in Safari.

VPS="root@157.230.91.33"
PORT=8050

# Reuse a working tunnel; otherwise replace a stale one
if ! curl -s -o /dev/null --max-time 3 "http://localhost:${PORT}/api/data"; then
  lsof -ti tcp:$PORT | xargs kill -9 2>/dev/null
  ssh -fNL ${PORT}:localhost:${PORT} $VPS
  sleep 1
fi

open -a Safari "http://localhost:${PORT}/visual"
echo "Visual Dashboard open at http://localhost:${PORT}/visual (Live Terminal: http://localhost:${PORT}/)"
echo "Close this window when done."
