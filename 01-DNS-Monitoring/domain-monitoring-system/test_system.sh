#!/bin/bash

# Domain Monitoring System - 系統測試腳本
# 用途: 快速檢查系統狀態並生成報告

echo "=========================================="
echo "🔍 Domain Monitoring System - 系統測試"
echo "=========================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 測試結果記錄
PASS=0
FAIL=0

# 函數: 測試項目
test_item() {
    local name=$1
    local command=$2
    
    echo -n "測試: $name ... "
    
    if eval "$command" > /tmp/dms_test_output.txt 2>&1; then
        echo -e "${GREEN}✓ 通過${NC}"
        PASS=$((PASS + 1))
        return 0
    else
        echo -e "${RED}✗ 失敗${NC}"
        FAIL=$((FAIL + 1))
        cat /tmp/dms_test_output.txt
        return 1
    fi
}

# 1. 檢查容器狀態
echo "📦 1. 檢查 Docker 容器狀態"
echo "----------------------------------------"
docker ps --filter "name=dms-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -v "PORTS"
echo ""

# 2. 測試 API 健康檢查
echo "🏥 2. API 健康檢查"
echo "----------------------------------------"
HEALTH=$(curl -s http://localhost:8000/health)
echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
echo ""

# 3. 檢查資料庫連接
echo "💾 3. 資料庫統計"
echo "----------------------------------------"
DB_STATS=$(docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -t -c "
SELECT 
    COUNT(*) as total_domains,
    COUNT(*) FILTER (WHERE is_active = true) as active_domains,
    COUNT(*) FILTER (WHERE is_active = false) as inactive_domains
FROM domains;
")
echo "域名統計: $DB_STATS"

ALERT_STATS=$(docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -t -c "
SELECT 
    COUNT(*) as total_alerts,
    COUNT(*) FILTER (WHERE is_resolved = false) as unresolved_alerts,
    COUNT(*) FILTER (WHERE alert_level = 'P0') as p0_alerts,
    COUNT(*) FILTER (WHERE alert_level = 'P1') as p1_alerts,
    COUNT(*) FILTER (WHERE alert_level = 'P2') as p2_alerts
FROM alerts;
")
echo "告警統計: $ALERT_STATS"
echo ""

# 4. 測試 API 端點
echo "🔌 4. API 端點測試"
echo "----------------------------------------"

# 4.1 域名列表
DOMAIN_COUNT=$(curl -s 'http://localhost:8000/api/domains' | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data))" 2>/dev/null)
if [ ! -z "$DOMAIN_COUNT" ]; then
    echo -e "${GREEN}✓${NC} GET /api/domains - 返回 $DOMAIN_COUNT 個域名"
else
    echo -e "${RED}✗${NC} GET /api/domains - 失敗"
fi

# 4.2 告警列表
ALERT_COUNT=$(curl -s 'http://localhost:8000/api/alerts?limit=100' | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data))" 2>/dev/null)
if [ ! -z "$ALERT_COUNT" ]; then
    echo -e "${GREEN}✓${NC} GET /api/alerts - 返回 $ALERT_COUNT 個告警"
else
    echo -e "${RED}✗${NC} GET /api/alerts - 失敗"
fi

# 4.3 監控事件
EVENT_COUNT=$(curl -s 'http://localhost:8000/api/events?limit=100' | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data))" 2>/dev/null)
if [ ! -z "$EVENT_COUNT" ]; then
    echo -e "${GREEN}✓${NC} GET /api/events - 返回 $EVENT_COUNT 個事件"
else
    echo -e "${RED}✗${NC} GET /api/events - 失敗"
fi

# 4.4 DNS 伺服器列表
NS_COUNT=$(curl -s 'http://localhost:8000/api/nameservers' | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data))" 2>/dev/null)
if [ ! -z "$NS_COUNT" ]; then
    echo -e "${GREEN}✓${NC} GET /api/nameservers - 返回 $NS_COUNT 個 DNS 伺服器"
else
    echo -e "${RED}✗${NC} GET /api/nameservers - 失敗"
fi

echo ""

# 5. 檢查告警內容(顯示域名)
echo "🔔 5. 最新告警 (前 5 筆)"
echo "----------------------------------------"
curl -s 'http://localhost:8000/api/alerts?limit=5' | python3 << 'PYEOF'
import sys, json
try:
    alerts = json.load(sys.stdin)
    if len(alerts) == 0:
        print("暫無告警 ✨")
    else:
        for i, alert in enumerate(alerts[:5], 1):
            domain_name = alert.get('domain_name', f"Domain #{alert.get('domain_id', 'Unknown')}")
            level = alert.get('alert_level', 'Unknown')
            cause = alert.get('root_cause', 'Unknown')
            print(f"{i}. [{level}] {domain_name} - {cause}")
except Exception as e:
    print(f"解析失敗: {e}")
PYEOF
echo ""

# 6. Celery 任務狀態
echo "⚙️  6. Celery 任務狀態"
echo "----------------------------------------"
echo "Celery Beat (最後 3 行):"
docker logs dms-celery-beat --tail 3 2>/dev/null | grep -v "WARN"
echo ""
echo "Celery Worker (最後 3 行):"
docker logs dms-celery-worker --tail 3 2>/dev/null | grep -v "WARN"
echo ""

# 7. 系統資源使用
echo "💻 7. 系統資源使用"
echo "----------------------------------------"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker ps --filter "name=dms-" -q) 2>/dev/null
echo ""

# 8. 最近監控活動
echo "📊 8. 最近監控活動"
echo "----------------------------------------"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -t -c "
SELECT 
    TO_CHAR(timestamp, 'HH24:MI:SS') as time,
    event_type,
    status,
    (SELECT domain FROM domains WHERE id = domain_id LIMIT 1) as domain
FROM monitoring_events 
ORDER BY timestamp DESC 
LIMIT 5;
" 2>/dev/null | head -5
echo ""

# 9. 生成測試報告
echo "=========================================="
echo "📋 測試報告摘要"
echo "=========================================="
echo "容器狀態: $(docker ps --filter 'name=dms-' --format '{{.Names}}' | wc -l | tr -d ' ') / 5 運行中"
echo "域名總數: ${DOMAIN_COUNT:-N/A}"
echo "告警數量: ${ALERT_COUNT:-N/A}"
echo "監控事件: ${EVENT_COUNT:-N/A}"
echo "DNS 伺服器: ${NS_COUNT:-N/A}"
echo ""
echo "儀表板: http://localhost:8000"
echo "API 文件: http://localhost:8000/docs"
echo ""
echo "=========================================="
echo "測試完成! $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# 清理臨時文件
rm -f /tmp/dms_test_output.txt

