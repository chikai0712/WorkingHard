#!/bin/bash

echo "🔧 配置 SecurityTrails API"
echo "=========================================="
echo ""

# 檢查 568win 相關域名數量
echo "1️⃣ 檢查 568win 相關域名數量:"
COUNT=$(docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -t -c "
SELECT COUNT(*) 
FROM domains 
WHERE domain LIKE '%568win%' 
AND is_active = true;
" | tr -d ' ')

echo "找到 $COUNT 個 568win 相關域名"
echo ""

# 列出這些域名
echo "2️⃣ 568win 相關域名列表:"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c "
SELECT domain, expected_ips, is_active 
FROM domains 
WHERE domain LIKE '%568win%' 
AND is_active = true
ORDER BY domain;
"

echo ""
echo "3️⃣ API 配額計算:"
echo "  - 每天檢查: $COUNT 個域名"
echo "  - 每個域名: 2 次 API 請求 (NS + WHOIS)"
echo "  - 每天消耗: $((COUNT * 2)) 次請求"
echo "  - 每月消耗: $((COUNT * 2 * 30)) 次請求"
echo "  - 免費額度: 50 次/月"
echo ""

if [ $((COUNT * 2 * 30)) -gt 50 ]; then
    echo "⚠️  警告: 每月消耗超過免費額度!"
    echo "建議: 只監控最重要的 1-2 個域名"
else
    echo "✅ 每月消耗在免費額度內"
fi

echo ""
echo "=========================================="
echo "📋 配置步驟"
echo "=========================================="
echo ""
echo "1. 訪問 https://securitytrails.com/ 註冊帳號"
echo "2. 前往 Account Settings → API"
echo "3. 點擊 Generate API Key"
echo "4. 複製 API Key"
echo "5. 編輯 docker-compose.yml:"
echo "   nano docker-compose.yml"
echo ""
echo "6. 找到 SECURITYTRAILS_API_KEY 並填入:"
echo "   - SECURITYTRAILS_API_KEY=your_api_key_here"
echo ""
echo "7. 重啟服務:"
echo "   docker-compose restart api celery-worker celery-beat"
echo ""
echo "8. 測試 API (手動觸發):"
echo "   docker exec -i dms-celery-worker celery -A app.tasks call check_568win_domains_securitytrails"
echo ""
echo "=========================================="
echo "⏰ 自動排程"
echo "=========================================="
echo ""
echo "系統會在每天凌晨 2:00 自動檢查 568win 域名的 NS 記錄"
echo "如果發現 NS 變動,會立即產生 P0 告警並發送通知"
echo ""

