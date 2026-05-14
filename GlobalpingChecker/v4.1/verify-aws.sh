#!/bin/bash

# AWS 部署驗證腳本
# 快速檢查 AWS 上的服務狀態

AWS_HOST="54.238.247.106"
PORT="8000"

echo "🔍 GlobalpingChecker V4.1 - AWS 驗證"
echo "===================================="
echo "目標: http://$AWS_HOST:$PORT"
echo ""

# 1. 測試連接
echo "1️⃣ 測試連接..."
if curl -s -f -m 5 http://$AWS_HOST:$PORT > /dev/null 2>&1; then
    echo "   ✅ 服務可訪問"
else
    echo "   ❌ 服務無法訪問"
    echo "   請檢查："
    echo "   - AWS 安全組是否開放端口 $PORT"
    echo "   - 服務是否正在運行"
    exit 1
fi

# 2. 測試 API Stats
echo "2️⃣ 測試 API Stats..."
STATS=$(curl -s -f -m 5 http://$AWS_HOST:$PORT/api/stats 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   ✅ API Stats 正常"
    echo "$STATS" | python3 -m json.tool 2>/dev/null | head -10
else
    echo "   ❌ API Stats 失敗"
    exit 1
fi

# 3. 測試批次列表
echo ""
echo "3️⃣ 測試批次列表..."
BATCHES=$(curl -s -f -m 5 http://$AWS_HOST:$PORT/api/batches 2>/dev/null)
if [ $? -eq 0 ]; then
    BATCH_COUNT=$(echo "$BATCHES" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
    echo "   ✅ 批次 API 正常 ($BATCH_COUNT 個批次)"
else
    echo "   ❌ 批次 API 失敗"
fi

# 4. 測試域名統計
echo ""
echo "4️⃣ 測試域名統計..."
ZONES=$(curl -s -f -m 5 http://$AWS_HOST:$PORT/api/stats 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"正常區: {data.get('normal_count', 0)}, 異常區: {data.get('abnormal_count', 0)}, 待分類: {data.get('pending_count', 0)}\")" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   ✅ $ZONES"
else
    echo "   ⚠️  無法獲取統計"
fi

# 5. 測試 Dashboard
echo ""
echo "5️⃣ 測試 Dashboard..."
if curl -s -f -m 5 http://$AWS_HOST:$PORT/ > /dev/null 2>&1; then
    echo "   ✅ Dashboard 可訪問"
else
    echo "   ❌ Dashboard 無法訪問"
fi

echo ""
echo "===================================="
echo "✅ AWS 驗證完成！"
echo ""
echo "📊 訪問 Dashboard:"
echo "   http://$AWS_HOST:$PORT"
echo ""
echo "📡 API 端點:"
echo "   Stats:   http://$AWS_HOST:$PORT/api/stats"
echo "   Batches: http://$AWS_HOST:$PORT/api/batches"
echo "   Docs:    http://$AWS_HOST:$PORT/docs"
echo ""
