#!/bin/bash

# 系統優化腳本

echo "🔧 Domain Monitoring System - 系統優化"
echo "=========================================="
echo ""

# 1. 重新建立 API (套用新的限制)
echo "1️⃣ 更新 API 配置..."
docker-compose build api
docker-compose restart api
echo "✅ API 已更新"
echo ""

# 等待 API 啟動
echo "⏳ 等待 API 啟動..."
sleep 5
echo ""

# 2. 列出無效域名
echo "2️⃣ 檢查無效域名..."
docker exec -i dms-api python manage_domains.py list
echo ""

# 3. 詢問是否停用
echo "是否要停用這些無法解析的域名? (y/N): "
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "3️⃣ 停用無效域名..."
    docker exec -i dms-api python manage_domains.py disable
    echo ""
else
    echo "⏭️  跳過停用域名"
    echo ""
fi

# 4. 解決重複告警
echo "4️⃣ 解決重複告警..."
docker exec -i dms-api python manage_domains.py resolve-dups
echo ""

# 5. 清理舊告警
echo "5️⃣ 清理舊告警..."
docker exec -i dms-api python manage_domains.py clean-alerts
echo ""

# 6. 顯示優化後的統計
echo "=========================================="
echo "📊 優化後統計"
echo "=========================================="
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -t -c "
SELECT 
    '域名總數: ' || COUNT(*) || ' 個' as stat
FROM domains
UNION ALL
SELECT 
    '啟用域名: ' || COUNT(*) || ' 個'
FROM domains WHERE is_active = true
UNION ALL
SELECT 
    '未解決告警: ' || COUNT(*) || ' 個'
FROM alerts WHERE is_resolved = false;
"
echo ""

echo "=========================================="
echo "✅ 優化完成!"
echo "=========================================="
echo ""
echo "🌐 開啟儀表板查看結果:"
echo "   http://localhost:8000"
echo ""

