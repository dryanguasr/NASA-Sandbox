#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec ros2 launch ros_gz_bridge ros_gz_bridge.launch.py config_file:="$PROJECT_ROOT/config/ros_gz_bridge.yaml"
