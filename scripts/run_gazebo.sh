#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if ! command -v gz >/dev/null 2>&1; then
  echo "Gazebo CLI missing. Install Gazebo Harmonic first." >&2
  exit 127
fi
export GZ_SIM_RESOURCE_PATH="$PROJECT_ROOT/models:${GZ_SIM_RESOURCE_PATH:-}"
exec gz sim -r -v 3 "$@" "$PROJECT_ROOT/worlds/mars_sandbox.sdf"
