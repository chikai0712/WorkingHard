#!/usr/bin/env bash
# 本機 BIND DNS - 建立 cache、logs 目錄並設定權限（供容器寫入）

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo "建立 cache、logs 目錄..."
mkdir -p cache logs
touch cache/.gitkeep logs/.gitkeep

# 讓 Docker 容器內 BIND 可寫入（本機開發用）
chmod 777 cache logs 2>/dev/null || true

echo "完成。可執行 ./scripts/start.sh 啟動 BIND。"
