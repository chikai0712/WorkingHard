#!/bin/bash

# 快速導入亞洲 ISP / 區域公開 DNS 列表（增量匯入，不刪除既有資料）

set -euo pipefail

echo "🌏 開始導入亞洲 ISP / 區域公開 DNS 列表（增量匯入）..."

SQL_FILE="dns_asia_isps_public.sql"

if [ ! -f "$SQL_FILE" ]; then
  echo "❌ 找不到 $SQL_FILE，請在專案根目錄執行此腳本"
  exit 1
fi

# 複製 SQL 文件到容器
echo "📋 複製 SQL 文件到資料庫容器..."
docker cp "$SQL_FILE" dms-postgres:/tmp/

# 執行導入
echo "⚙️  執行 SQL 導入..."
docker-compose exec -T postgres psql -U dms_user -d domain_monitoring -f "/tmp/$SQL_FILE"

# 驗證導入結果
echo ""
echo "✅ 驗證導入結果（亞洲國家/地區）..."
echo ""
docker-compose exec -T postgres psql -U dms_user -d domain_monitoring -c "SELECT country_code, COUNT(*) as count FROM nameservers WHERE country_code IN ('TW','HK','JP','KR','SG','MY','CN') GROUP BY country_code ORDER BY count DESC;"

echo ""
echo "🎉 導入完成！"
echo ""
echo "📊 查看 Dashboard 頁面："
echo "   http://localhost:8000/"
echo "   然後點擊 '🌐 DNS 監控器' 標籤，並用國家按鈕篩選"
echo ""


