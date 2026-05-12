#!/bin/bash

echo "🧪 Uptime 監控驗證測試"
echo "=========================================="
echo ""

# 1. 檢查 568win 域名的關鍵字設定
echo "1️⃣ 檢查域名關鍵字設定:"
echo "----------------------------------------"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c "
SELECT domain, keyword, is_active 
FROM domains 
WHERE domain LIKE '%568win%' 
AND is_active = true
ORDER BY domain;
"

echo ""
echo "2️⃣ 手動測試單一域名 (使用 Python):"
echo "----------------------------------------"
docker exec -i dms-api python3 << 'PYEOF'
import asyncio
import sys
sys.path.insert(0, '/app')

from app.uptime_checker import UptimeChecker

async def test_uptime():
    checker = UptimeChecker()
    
    # 測試一個 568win 域名
    test_domains = ['568win.com', '568win.net', '568win.co']
    
    for domain in test_domains:
        print(f"\n測試域名: {domain}")
        print("-" * 50)
        
        result = await checker.check_multiple_protocols(domain, keyword='568')
        
        best = result['best_result']
        
        print(f"  協議: {result['best_protocol']}")
        print(f"  可用: {'✅' if best.get('available') else '❌'}")
        
        if best.get('available'):
            print(f"  HTTP 狀態: {best.get('http_status')}")
            print(f"  響應時間: {best.get('response_time_ms')} ms")
            print(f"  內容長度: {best.get('content_length')} bytes")
            
            if best.get('keyword_expected'):
                keyword_status = '✅' if best.get('keyword_match') else '❌'
                print(f"  關鍵字匹配: {keyword_status} (預期: '{best.get('keyword_expected')}')")
        else:
            print(f"  錯誤: {best.get('error', 'Unknown')}")

asyncio.run(test_uptime())
PYEOF

echo ""
echo "3️⃣ 手動觸發 Celery 任務:"
echo "----------------------------------------"
echo "觸發 568win Uptime 檢查任務..."
docker exec -i dms-celery-worker celery -A app.tasks call check_568win_uptime --timeout=60

echo ""
echo "⏳ 等待 5 秒讓任務完成..."
sleep 5

echo ""
echo "4️⃣ 檢查 Uptime 監控事件記錄:"
echo "----------------------------------------"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c "
SELECT 
    d.domain,
    me.status,
    me.details->>'best_protocol' as protocol,
    me.details->'best_result'->>'http_status' as http_status,
    me.details->'best_result'->>'available' as available,
    me.details->'best_result'->>'keyword_match' as keyword_match,
    me.details->'best_result'->>'response_time_ms' as response_ms,
    TO_CHAR(me.timestamp, 'HH24:MI:SS') as time
FROM monitoring_events me
JOIN domains d ON d.id = me.domain_id
WHERE me.event_type = 'uptime_check'
AND d.domain LIKE '%568win%'
ORDER BY me.timestamp DESC
LIMIT 10;
"

echo ""
echo "5️⃣ 檢查是否產生 Uptime 相關告警:"
echo "----------------------------------------"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c "
SELECT 
    d.domain,
    a.alert_level,
    a.root_cause,
    a.is_resolved,
    TO_CHAR(a.first_seen, 'YYYY-MM-DD HH24:MI:SS') as first_seen,
    TO_CHAR(a.last_seen, 'HH24:MI:SS') as last_seen
FROM alerts a
JOIN domains d ON d.id = a.domain_id
WHERE d.domain LIKE '%568win%'
AND a.root_cause IN ('content_defacement', 'service_down')
ORDER BY a.last_seen DESC
LIMIT 5;
" 2>/dev/null || echo "尚無 Uptime 相關告警"

echo ""
echo "6️⃣ 檢查 Celery Beat 排程:"
echo "----------------------------------------"
echo "查看 Celery Beat 日誌 (最後 20 行):"
docker logs dms-celery-beat --tail 20 | grep -E "check_568win_uptime|Scheduler"

echo ""
echo "7️⃣ 檢查 Celery Worker 狀態:"
echo "----------------------------------------"
docker exec -i dms-celery-worker celery -A app.tasks inspect active | head -20

echo ""
echo "8️⃣ 統計 Uptime 檢查結果:"
echo "----------------------------------------"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c "
SELECT 
    COUNT(*) as total_checks,
    COUNT(*) FILTER (WHERE status = 'ok') as ok_count,
    COUNT(*) FILTER (WHERE status = 'warning') as warning_count,
    COUNT(*) FILTER (WHERE status = 'critical') as critical_count,
    TO_CHAR(MIN(timestamp), 'YYYY-MM-DD HH24:MI:SS') as first_check,
    TO_CHAR(MAX(timestamp), 'YYYY-MM-DD HH24:MI:SS') as last_check
FROM monitoring_events
WHERE event_type = 'uptime_check';
"

echo ""
echo "=========================================="
echo "📋 驗證結果總結"
echo "=========================================="
echo ""

# 檢查是否有 Uptime 記錄
UPTIME_COUNT=$(docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -t -c "
SELECT COUNT(*) FROM monitoring_events WHERE event_type = 'uptime_check';
" | tr -d ' ')

if [ "$UPTIME_COUNT" -gt 0 ]; then
    echo "✅ Uptime 監控正常運作!"
    echo "   - 已執行 $UPTIME_COUNT 次檢查"
    echo "   - 監控事件已記錄到資料庫"
else
    echo "⚠️  尚未執行 Uptime 檢查"
    echo ""
    echo "可能原因:"
    echo "1. Celery Worker 未啟動"
    echo "2. 任務排程未生效"
    echo "3. 沒有 568win 域名或都已停用"
    echo ""
    echo "解決方法:"
    echo "1. 重啟服務: docker-compose restart celery-worker celery-beat"
    echo "2. 手動觸發: docker exec -i dms-celery-worker celery -A app.tasks call check_568win_uptime"
    echo "3. 檢查日誌: docker logs dms-celery-worker --tail 50"
fi

echo ""
echo "=========================================="
echo "🔄 持續監控"
echo "=========================================="
echo ""
echo "Uptime 監控會每 10 分鐘自動執行"
echo "查看即時日誌:"
echo "  docker logs -f dms-celery-worker"
echo ""
echo "查看最新檢查結果:"
echo "  ./setup_uptime.sh"
echo ""





