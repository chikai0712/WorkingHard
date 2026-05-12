#!/bin/bash

# DNS 測試腳本
# 測試 BIND DNS 服務是否正常運行

set -e

echo "🧪 測試 BIND DNS 服務..."
echo ""

# 檢查容器是否運行
if ! docker ps | grep -q bind9-dns; then
    echo "❌ 錯誤: BIND DNS 容器未運行"
    echo "   請先執行: ./start.sh"
    exit 1
fi

echo "✅ 容器運行中"
echo ""

# 測試本地 DNS 查詢
echo "📡 測試 DNS 查詢..."

# 測試 example.com (如果配置了)
if dig @127.0.0.1 example.com +short 2>/dev/null | grep -q .; then
    echo "✅ example.com 查詢成功:"
    dig @127.0.0.1 example.com +short
else
    echo "⚠️  example.com 未配置或查詢失敗"
fi

echo ""

# 測試遞迴查詢（查詢外部域名）
echo "🌐 測試遞迴查詢（google.com）..."
if dig @127.0.0.1 google.com +short 2>/dev/null | grep -q .; then
    echo "✅ 遞迴查詢成功:"
    dig @127.0.0.1 google.com +short | head -1
else
    echo "⚠️  遞迴查詢失敗（可能是配置限制）"
fi

echo ""

# 檢查日誌
echo "📝 最近的日誌（最後 10 行）:"
docker-compose logs --tail=10 bind9

echo ""
echo "✅ 測試完成"

