#!/usr/bin/env bash
# 本機 BIND DNS - 停止並移除 BIND 容器

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo "停止 BIND 容器..."
docker compose down

echo "已停止。"
