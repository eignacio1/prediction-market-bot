#!/usr/bin/env bash
# Install / uninstall the weekly evidence copy (Sunday 03:00 local; a missed run fires on wake). Run on the Mac.
#   install:   scripts/ops/evidence_pull_launchd.sh install     (only after the operator says yes)
#   uninstall: scripts/ops/evidence_pull_launchd.sh uninstall   (== launchctl bootout gui/$(id -u)/com.predictionmarket.evidence-pull && rm ~/Library/LaunchAgents/com.predictionmarket.evidence-pull.plist)
set -euo pipefail
L=com.predictionmarket.evidence-pull; DST="$HOME/Library/LaunchAgents/$L.plist"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
case "${1:-}" in
  install) mkdir -p "$HOME/Library/LaunchAgents" "$HOME/PredictionMarketEvidence/_manifests"
    sed -e "s|__REPO__|$REPO|g" -e "s|__HOME__|$HOME|g" "$REPO/scripts/ops/$L.plist" > "$DST"
    launchctl bootout "gui/$(id -u)/$L" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$DST"; echo "installed $L" ;;
  uninstall) launchctl bootout "gui/$(id -u)/$L" 2>/dev/null || true; rm -f "$DST"; echo "removed $L" ;;
  *) echo "usage: $0 install|uninstall" >&2; exit 2 ;;
esac
