#!/bin/bash

echo "🌐 配置 Uptime 監控"
echo "=========================================="
echo ""

# 檢查 568win 相關域名
echo "1️⃣ 檢查 568win 相關域名:"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c "
SELECT domain, keyword, is_active 
FROM domains 
WHERE domain LIKE '%568win%' 
AND is_active = true
ORDER BY domain;
"

echo ""
echo "2️⃣ 設定關鍵字監控"
echo "=========================================="
echo ""
echo "為了檢測網頁內容是否被竄改,需要為每個域名設定關鍵字"
echo ""
echo "範例:"
echo "  - 如果網站首頁有 'Welcome to 568win' → 設定關鍵字: 'Welcome'"
echo "  - 如果網站有 '立即註冊' → 設定關鍵字: '立即註冊'"
echo "  - 如果網站有 logo 文字 '568WIN' → 設定關鍵字: '568WIN'"
echo ""
echo "建議: 選擇網站中不太會變動的文字作為關鍵字"
echo ""

# 提供設定關鍵字的 SQL 範例
echo "3️⃣ 設定關鍵字 SQL 範例:"
echo "=========================================="
echo ""
echo "# 為單一域名設定關鍵字:"
echo "docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c \\"
echo "  \"UPDATE domains SET keyword = 'Welcome' WHERE domain = '568win.com';\""
echo ""
echo "# 為所有 568win 域名設定相同關鍵字:"
echo "docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c \\"
echo "  \"UPDATE domains SET keyword = '568WIN' WHERE domain LIKE '%568win%';\""
echo ""

# 測試 Uptime 檢查
echo "4️⃣ 測試 Uptime 檢查:"
echo "=========================================="
echo ""
echo "手動觸發一次檢查:"
echo "  docker exec -i dms-celery-worker celery -A app.tasks call check_568win_uptime"
echo ""

# 監控頻率說明
echo "5️⃣ 監控頻率:"
echo "=========================================="
echo ""
echo "✅ DNS 檢查: 每 5 分鐘 (所有域名)"
echo "✅ Uptime 檢查: 每 10 分鐘 (568win 域名)"
echo "✅ SecurityTrails: 每天凌晨 2:00 (568win 域名)"
echo ""

# 告警邏輯說明
echo "6️⃣ Uptime 告警邏輯:"
echo "=========================================="
echo ""
echo "P1 告警 - 內容竄改:"
echo "  - DNS 解析正常"
echo "  - 網站可訪問 (HTTP 200)"
echo "  - 但關鍵字不匹配"
echo "  → 可能網站內容被竄改"
echo ""
echo "P2 告警 - 網站無法訪問:"
echo "  - HTTP 錯誤 (4xx, 5xx)"
echo "  - 連線超時"
echo "  - 連線失敗"
echo "  → 網站服務異常"
echo ""

# 查看最近的 Uptime 檢查結果
echo "7️⃣ 查看最近的 Uptime 檢查結果:"
echo "=========================================="
echo ""
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c "
SELECT 
    d.domain,
    me.status,
    me.details->>'best_protocol' as protocol,
    me.details->'best_result'->>'http_status' as http_status,
    me.details->'best_result'->>'keyword_match' as keyword_match,
    TO_CHAR(me.timestamp, 'YYYY-MM-DD HH24:MI:SS') as check_time
FROM monitoring_events me
JOIN domains d ON d.id = me.domain_id
WHERE me.event_type = 'uptime_check'
AND d.domain LIKE '%568win%'
ORDER BY me.timestamp DESC
LIMIT 10;
" 2>/dev/null || echo "尚無 Uptime 檢查記錄"

echo ""
echo "=========================================="
echo "✅ Uptime 監控配置完成!"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. 為域名設定關鍵字 (使用上面的 SQL 範例)"
echo "2. 重啟服務: docker-compose restart celery-worker celery-beat"
echo "3. 等待 10 分鐘後查看檢查結果"
echo "4. 查看儀表板: http://localhost:8000"
echo ""

