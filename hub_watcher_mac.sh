#!/bin/bash
# hub_watcher_mac.sh - Watcher para Norte (Mac) via launchd.
# Norte lee briefs por SSH a la PC y escribe consensos por scp.
HUB_REMOTE="arijd@192.168.0.11"
HUB_WIN="C:/Users/arijd/Documents/Atlas/HUB"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

python3 "$SCRIPT_DIR/hub_dispatch.py" \
    --agent norte \
    --hub-path "$SCRIPT_DIR" \
    --remote "$HUB_REMOTE" \
    2>&1 | tee -a "$SCRIPT_DIR/.dispatch_norte.log"
