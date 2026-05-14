#!/bin/bash

# 快速導入越南和印尼 DNS 列表

echo "🌐 開始導入越南和印尼 DNS 列表..."

# 複製 SQL 文件到容器
echo "📋 複製 SQL 文件到資料庫容器..."
docker cp dns_vietnam_indonesia.sql dms-postgres:/tmp/

# 執行導入
echo "⚙️  執行 SQL 導入..."
docker-compose exec -T postgres psql -U dms_user -d domain_monitoring -f /tmp/dns_vietnam_indonesia.sql

# 驗證導入結果
echo ""
echo "✅ 驗證導入結果..."
echo ""
docker-compose exec -T postgres psql -U dms_user -d domain_monitoring -c "SELECT country_code, COUNT(*) as count FROM nameservers WHERE country_code IN ('VN', 'ID') GROUP BY country_code;"

echo ""
echo "🎉 導入完成！"
echo ""
echo "📊 查看 Dashboard 頁面："
echo "   http://localhost:8000/"
echo "   然後點擊 '🌐 DNS 監控器' 標籤"
echo ""
echo "🌏 如需導入更多亞洲國家/地區 DNS（增量、不刪除 VN/ID）："
echo "   ./import_dns_asia_quick.sh"
echo ""

