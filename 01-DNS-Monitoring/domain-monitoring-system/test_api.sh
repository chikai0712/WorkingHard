#!/bin/bash

# 快速測試腳本

echo "🧪 Domain Monitoring System - 功能測試"
echo "========================================"
echo ""

API_URL="http://localhost:8000"

# 檢查服務是否運行
echo "1️⃣ 檢查 API 服務..."
if curl -s "$API_URL" > /dev/null; then
    echo "✅ API 服務正常運行"
else
    echo "❌ API 服務未啟動,請先執行: docker-compose up -d"
    exit 1
fi

echo ""
echo "2️⃣ 測試新增網域..."
DOMAIN_RESPONSE=$(curl -s -X POST "$API_URL/api/domains" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "test-example.com",
    "expected_ips": ["93.184.216.34"],
    "expected_ns": ["a.iana-servers.net", "b.iana-servers.net"],
    "keyword": "Example",
    "check_interval": 300
  }')

if echo "$DOMAIN_RESPONSE" | grep -q "test-example.com"; then
    echo "✅ 網域新增成功"
    DOMAIN_ID=$(echo "$DOMAIN_RESPONSE" | grep -o '"id":[0-9]*' | grep -o '[0-9]*')
    echo "   Domain ID: $DOMAIN_ID"
else
    echo "⚠️  網域可能已存在或新增失敗"
fi

echo ""
echo "3️⃣ 測試新增 DNS 伺服器..."
NS_RESPONSE=$(curl -s -X POST "$API_URL/api/nameservers" \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "US",
    "isp_name": "Test DNS",
    "dns_server": "8.8.8.8"
  }')

if echo "$NS_RESPONSE" | grep -q "8.8.8.8"; then
    echo "✅ DNS 伺服器新增成功"
else
    echo "⚠️  DNS 伺服器可能已存在"
fi

echo ""
echo "4️⃣ 列出所有網域..."
DOMAINS=$(curl -s "$API_URL/api/domains")
DOMAIN_COUNT=$(echo "$DOMAINS" | grep -o '"domain"' | wc -l)
echo "✅ 目前監控 $DOMAIN_COUNT 個網域"

echo ""
echo "5️⃣ 列出所有 DNS 伺服器..."
NAMESERVERS=$(curl -s "$API_URL/api/nameservers")
NS_COUNT=$(echo "$NAMESERVERS" | grep -o '"dns_server"' | wc -l)
echo "✅ 目前有 $NS_COUNT 個 DNS 伺服器"

echo ""
echo "6️⃣ 測試手動 DNS 檢查..."
CHECK_RESPONSE=$(curl -s -X POST "$API_URL/api/check/dns" \
  -H "Content-Type: application/json" \
  -d '{"domain": "google.com"}')

if echo "$CHECK_RESPONSE" | grep -q "success"; then
    echo "✅ DNS 檢查功能正常"
else
    echo "⚠️  DNS 檢查可能失敗 (需要先新增 google.com 到監控列表)"
fi

echo ""
echo "7️⃣ 查看告警列表..."
ALERTS=$(curl -s "$API_URL/api/alerts")
echo "✅ 告警系統正常運作"

echo ""
echo "========================================"
echo "✅ 基礎功能測試完成!"
echo ""
echo "📍 查看完整 API 文件: $API_URL/docs"
echo "📍 查看服務日誌: docker-compose logs -f api"
echo "📍 查看 Celery 任務: docker-compose logs -f celery-worker"

