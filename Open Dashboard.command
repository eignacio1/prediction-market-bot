#!/bin/bash
# PMBot Dashboard — double-click to open
# Opens the SSH tunnel and launches the dashboard in your browser.
# The VPS server must be running (one-time setup already done).

VPS="root@157.230.91.33"
PORT=8050

# Kill any stale tunnel on this port first
lsof -ti tcp:$PORT | xargs kill -9 2>/dev/null

# Open fresh SSH tunnel in background
ssh -fNL ${PORT}:localhost:${PORT} $VPS

# Give the tunnel a moment to establish
sleep 1

# Open browser
open http://localhost:${PORT}

echo "Dashboard open at http://localhost:${PORT}"
echo "Close this window when done."
