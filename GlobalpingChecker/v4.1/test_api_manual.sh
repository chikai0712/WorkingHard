#!/bin/bash
# 手動測試 Globalping API
# 在允許外網訪問的環境中運行此腳本

TOKEN="uh5vlg4ttg3v5gwby5zgtqrciimahql5"
API_URL="https://api.globalping.io/v1"

echo "=========================================="
echo "🔍 Globalping API 手動測試"
echo "=========================================="
echo ""

# 1. 測試 API 連接和額度
echo "1️⃣  測試 API 連接 - 獲取額度信息"
echo "------------------------------------------"
curl -s -X GET \
  "${API_URL}/limits" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" | jq . 2>/dev/null || echo "無法解析 JSON，原始輸出："

echo ""
echo ""

# 2. 測試創建測量（測試一個域名）
echo "2️⃣  測試創建測量 - 檢測 example.com"
echo "------------------------------------------"
curl -s -X POST \
  "${API_URL}/measurements" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "http",
    "target": "example.com",
    "inProgressUpdates": false,
    "options": {
      "method": "HEAD"
    }
  }' | jq . 2>/dev/null || echo "無法解析 JSON，原始輸出："

echo ""
echo ""

# 3. 測試獲取測量結果
echo "3️⃣  測試獲取最近的測量結果"
echo "------------------------------------------"
curl -s -X GET \
  "${API_URL}/measurements?limit=1" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" | jq . 2>/dev/null || echo "無法解析 JSON，原始輸出："

echo ""
echo "=========================================="
echo "✅ 測試完成"
echo "=========================================="
