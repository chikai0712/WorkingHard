#!/bin/bash

# 快速測試 Globalping API Token

echo "🔍 測試 Globalping API Token"
echo "========================================"
echo ""

# 測試 Token（不含前綴）
echo "測試 1: 不含前綴的 Token"
curl -s -H "Authorization: Bearer uh5vlg4ttg3v5gwby5zgtqrciimahql5" \
  https://api.globalping.io/v1/limits | python3 -m json.tool

echo ""
echo "========================================"
echo ""

# 測試 Token（含 gp_ 前綴）
echo "測試 2: 含 gp_ 前綴的 Token"
curl -s -H "Authorization: Bearer gp_uh5vlg4ttg3v5gwby5zgtqrciimahql5" \
  https://api.globalping.io/v1/limits | python3 -m json.tool

echo ""
echo "========================================"
echo "✅ 測試完成"
echo ""
echo "請查看哪個格式返回了正確的數據"
