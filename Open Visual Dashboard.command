#!/bin/bash
# Opens the PMBot Visual Dashboard in Safari: a self-contained file next to this launcher, built by
# scripts/build_visual_dashboard_html.py from 04_EXECUTION/visual_dashboard/ (refreshed at each wave close).
DIR="$(cd "$(dirname "$0")" && pwd)"
open -a Safari "$DIR/PMBot Visual Dashboard.html"
