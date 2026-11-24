#!/usr/bin/env bash
# orchestrator-loop.sh — Infinite loop that invokes the issue-orchestrator
# every N minutes via `opencode run`, streaming output to the terminal.
#
# Usage:
#   ./scripts/orchestrator-loop.sh [interval_seconds] [base_branch] [integration_branch]
#
# Examples:
#   ./scripts/orchestrator-loop.sh            # 300s, main, feature/issue-<n>
#   ./scripts/orchestrator-loop.sh 600        # 10 min poll
#   ./scripts/orchestrator-loop.sh 300 main feature/issue-<n>

set -euo pipefail

INTERVAL=${1:-300}
BASE_BRANCH=${2:-main}
INTEGRATION_BRANCH=${3:-feature/issue-<n>}

cd "$(dirname "$0")/.."

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Running issue-orchestrator (base=$BASE_BRANCH, branch=$INTEGRATION_BRANCH) ==="
    stdbuf -oL opencode run "@issue-orchestrator --base_branch=$BASE_BRANCH --integration_branch=$INTEGRATION_BRANCH"
    echo ""
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Done. Sleeping ${INTERVAL}s ==="
    sleep "$INTERVAL"
done
