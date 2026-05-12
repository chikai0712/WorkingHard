#!/usr/bin/env bash
# 本機 BIND DNS - 啟動 BIND 容器

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

if [ ! -d cache ]; then
    mkdir -p cache logs
    chmod 777 cache logs 2>/dev/null || true
fi

echo "啟動 BIND 容器 (bind-dns-local)..."
docker compose up -d

echo ""
echo "BIND 已在本機 127.0.0.1:53 監聽。"
echo "查詢範例: dig @127.0.0.1 example.com"
echo "或執行: ./scripts/test-dns.sh"
