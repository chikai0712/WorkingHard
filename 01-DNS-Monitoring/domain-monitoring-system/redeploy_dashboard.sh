#!/bin/bash

echo "🔄 重新部署儀表板"
echo "=========================================="

# 1. 重建 API 容器
echo "1️⃣ 重建 API 容器..."
docker-compose build api
docker-compose restart api

echo ""
echo "⏳ 等待 API 啟動..."
sleep 5

# 2. 測試 API 是否返回域名
echo ""
echo "2️⃣ 測試 API 返回的告警資料:"
curl -s 'http://localhost:8000/api/alerts?limit=3' | python3 -m json.tool | head -30

echo ""
echo "=========================================="
echo "✅ 部署完成!"
echo "=========================================="
echo ""
echo "請執行以下步驟:"
echo "1. 開啟瀏覽器"
echo "2. 按 Cmd+Shift+R (Mac) 或 Ctrl+Shift+R (Windows) 強制重新整理"
echo "3. 或清除瀏覽器緩存後重新開啟 http://localhost:8000"
echo ""

