#!/bin/bash

# 快速開啟系統終端並執行 AWS 管理

echo "🚀 開啟系統終端..."
echo ""
echo "由於 Cursor 代理限制，將在系統終端執行 AWS 操作"
echo ""

# 獲取腳本目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 使用 open 命令開啟終端並執行命令
open -a Terminal.app "$SCRIPT_DIR"

echo "✅ 已開啟系統終端"
echo ""
echo "在新開啟的終端中執行："
echo "  ./check-status.sh    # 檢查狀態"
echo "  ./aws-manager.sh     # 管理界面"
echo ""
