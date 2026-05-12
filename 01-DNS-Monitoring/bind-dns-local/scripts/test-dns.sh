#!/usr/bin/env bash
# 本機 BIND DNS - 查詢測試（example.com、localhost）

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

RESOLVER="${1:-127.0.0.1}"
PORT="${2:-53}"

echo "查詢本機 BIND @ $RESOLVER:$PORT"
echo "----------------------------------------"

echo "1. example.com A"
dig @"$RESOLVER" -p "$PORT" example.com A +short
echo ""

echo "2. www.example.com A"
dig @"$RESOLVER" -p "$PORT" www.example.com A +short
echo ""

echo "3. localhost A"
dig @"$RESOLVER" -p "$PORT" localhost A +short
echo ""

echo "4. example.com AXFR（若未開放則會失敗，屬正常）"
dig @"$RESOLVER" -p "$PORT" example.com AXFR +short 2>&1 | head -5
echo "----------------------------------------"
echo "測試完成。"
