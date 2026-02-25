#!/bin/bash

# DNS 監控系統檢查腳本
# 用途：驗證第一項 DNS 檢查任務是否正確執行

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  🔍 DNS 監控系統檢查報告"
echo "=========================================="
echo ""

# 步驟 1: 檢查服務狀態
echo -e "${BLUE}[步驟 1]${NC} 檢查 Docker 容器狀態..."
echo "----------------------------------------"
docker-compose ps
echo ""

# 檢查關鍵容器是否運行
API_STATUS=$(docker-compose ps -q api 2>/dev/null)
WORKER_STATUS=$(docker-compose ps -q celery-worker 2>/dev/null)
BEAT_STATUS=$(docker-compose ps -q celery-beat 2>/dev/null)

if [ -z "$API_STATUS" ] || [ -z "$WORKER_STATUS" ] || [ -z "$BEAT_STATUS" ]; then
    echo -e "${RED}❌ 部分服務未運行，正在啟動...${NC}"
    docker-compose up -d
    echo "等待服務啟動..."
    sleep 10
else
    echo -e "${GREEN}✅ 所有服務正在運行${NC}"
fi
echo ""

# 步驟 2: 檢查 API 健康狀態
echo -e "${BLUE}[步驟 2]${NC} 檢查 API 健康狀態..."
echo "----------------------------------------"
HEALTH_CHECK=$(curl -s http://localhost:8000/health 2>/dev/null || echo "")
if [ -n "$HEALTH_CHECK" ]; then
    echo -e "${GREEN}✅ API 服務正常${NC}"
    echo "$HEALTH_CHECK" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_CHECK"
else
    echo -e "${RED}❌ API 服務無法訪問${NC}"
    echo "請檢查服務是否正常啟動"
    exit 1
fi
echo ""

# 步驟 3: 查看資料庫狀態
echo -e "${BLUE}[步驟 3]${NC} 查看資料庫狀態..."
echo "----------------------------------------"
docker-compose exec -T api python3 << 'PYTHON_SCRIPT'
from app.database import SessionLocal
from app.models import Domain, MonitoringEvent, Nameserver, Alert
from datetime import datetime, timedelta

db = SessionLocal()

# 統計資訊
domain_count = db.query(Domain).count()
active_domain_count = db.query(Domain).filter(Domain.is_active == True).count()
nameserver_count = db.query(Nameserver).count()
healthy_ns_count = db.query(Nameserver).filter(Nameserver.is_healthy == True).count()
event_count = db.query(MonitoringEvent).count()
alert_count = db.query(Alert).filter(Alert.is_resolved == False).count()

print(f"📊 資料庫統計：")
print(f"  - 監控網域總數: {domain_count} (啟用: {active_domain_count})")
print(f"  - DNS 伺服器總數: {nameserver_count} (健康: {healthy_ns_count})")
print(f"  - 監控事件總數: {event_count}")
print(f"  - 未解決告警數: {alert_count}")
print()

# 列出所有網域
if domain_count > 0:
    print("📋 監控網域列表：")
    domains = db.query(Domain).all()
    for d in domains:
        status = "✅ 啟用" if d.is_active else "❌ 停用"
        print(f"  {status} {d.domain}")
        print(f"      預期 IP: {', '.join(d.expected_ips)}")
        print(f"      預期 NS: {', '.join(d.expected_ns)}")
        if d.keyword:
            print(f"      關鍵字: {d.keyword}")
    print()
else:
    print("⚠️  尚未新增任何監控網域")
    print()

# 列出 DNS 伺服器
if nameserver_count > 0:
    print("🌐 DNS 伺服器列表：")
    nameservers = db.query(Nameserver).all()
    for ns in nameservers:
        health = "✅ 健康" if ns.is_healthy else "❌ 不健康"
        response_time = f"{ns.response_time_ms}ms" if ns.response_time_ms else "N/A"
        print(f"  {health} [{ns.country_code}] {ns.isp_name}: {ns.dns_server} (回應: {response_time})")
    print()
else:
    print("⚠️  尚未新增任何 DNS 伺服器")
    print()

# 最近的監控事件
recent_events = db.query(MonitoringEvent).order_by(MonitoringEvent.timestamp.desc()).limit(10).all()
if recent_events:
    print("📝 最近 10 筆監控事件：")
    for e in recent_events:
        status_icon = "✅" if e.status == "ok" else "⚠️" if e.status == "warning" else "❌"
        print(f"  {status_icon} {e.timestamp} | {e.event_type} | {e.status}")
        if e.event_type == 'dns_check' and e.details:
            success_rate = e.details.get('success_rate', 0)
            print(f"      成功率: {success_rate*100:.1f}%")
    print()
else:
    print("⚠️  尚無監控事件記錄")
    print()

# 未解決的告警
unresolved_alerts = db.query(Alert).filter(Alert.is_resolved == False).all()
if unresolved_alerts:
    print("🚨 未解決的告警：")
    for a in unresolved_alerts:
        level_icon = "🚨" if a.alert_level == "P0" else "⚠️" if a.alert_level == "P1" else "ℹ️"
        domain = db.query(Domain).filter(Domain.id == a.domain_id).first()
        domain_name = domain.domain if domain else "Unknown"
        print(f"  {level_icon} [{a.alert_level}] {domain_name}")
        print(f"      根因: {a.root_cause}")
        print(f"      首次發現: {a.first_seen}")
        print(f"      最後發現: {a.last_seen}")
    print()
else:
    print("✅ 目前沒有未解決的告警")
    print()

db.close()
PYTHON_SCRIPT
echo ""

# 步驟 4: 查看 Celery Beat 調度日誌
echo -e "${BLUE}[步驟 4]${NC} 查看 Celery Beat 調度日誌（最近 20 行）..."
echo "----------------------------------------"
docker-compose logs --tail=20 celery-beat | grep -E "Scheduler|check-all-domains|check.*568win" || echo "⚠️  未找到相關調度記錄"
echo ""

# 步驟 5: 查看 Celery Worker 執行日誌
echo -e "${BLUE}[步驟 5]${NC} 查看 Celery Worker 執行日誌（最近 30 行）..."
echo "----------------------------------------"
docker-compose logs --tail=30 celery-worker | grep -E "check_all_domains|check_single_domain|Checked domain" || echo "⚠️  未找到相關執行記錄"
echo ""

# 步驟 6: 測試手動觸發 DNS 檢查
echo -e "${BLUE}[步驟 6]${NC} 測試手動觸發 DNS 檢查..."
echo "----------------------------------------"

# 檢查是否有網域和 DNS 伺服器
DOMAIN_COUNT=$(docker-compose exec -T api python3 -c "from app.database import SessionLocal; from app.models import Domain; db = SessionLocal(); print(db.query(Domain).filter(Domain.is_active == True).count())")
NS_COUNT=$(docker-compose exec -T api python3 -c "from app.database import SessionLocal; from app.models import Nameserver; db = SessionLocal(); print(db.query(Nameserver).filter(Nameserver.is_healthy == True).count())")

if [ "$DOMAIN_COUNT" -gt 0 ] && [ "$NS_COUNT" -gt 0 ]; then
    echo "正在手動觸發 DNS 檢查..."
    
    # 獲取第一個網域
    FIRST_DOMAIN=$(docker-compose exec -T api python3 -c "from app.database import SessionLocal; from app.models import Domain; db = SessionLocal(); d = db.query(Domain).filter(Domain.is_active == True).first(); print(d.domain if d else '')")
    
    if [ -n "$FIRST_DOMAIN" ]; then
        echo "測試網域: $FIRST_DOMAIN"
        
        # 手動觸發檢查
        RESULT=$(curl -s -X POST http://localhost:8000/api/check/dns \
          -H "Content-Type: application/json" \
          -d "{\"domain\": \"$FIRST_DOMAIN\"}" 2>/dev/null || echo "")
        
        if [ -n "$RESULT" ]; then
            echo -e "${GREEN}✅ 手動檢查成功${NC}"
            echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"
        else
            echo -e "${RED}❌ 手動檢查失敗${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  無法測試：需要至少 1 個網域和 1 個 DNS 伺服器${NC}"
    echo ""
    echo "建議執行以下命令新增測試資料："
    echo ""
    echo "# 新增 Google DNS"
    echo "curl -X POST http://localhost:8000/api/nameservers \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -d '{\"country_code\": \"US\", \"isp_name\": \"Google\", \"dns_server\": \"8.8.8.8\"}'"
    echo ""
    echo "# 新增測試網域"
    echo "curl -X POST http://localhost:8000/api/domains \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -d '{\"domain\": \"google.com\", \"expected_ips\": [\"142.250.185.46\"], \"expected_ns\": [\"ns1.google.com\"], \"keyword\": \"Google\"}'"
fi
echo ""

# 步驟 7: 檢查定時任務配置
echo -e "${BLUE}[步驟 7]${NC} 檢查定時任務配置..."
echo "----------------------------------------"
docker-compose exec -T api python3 << 'PYTHON_SCRIPT'
from app.tasks import celery_app

print("📅 已配置的定時任務：")
print()
for task_name, task_config in celery_app.conf.beat_schedule.items():
    task = task_config['task']
    schedule = task_config['schedule']
    
    if hasattr(schedule, 'run_every'):
        interval = schedule.run_every.total_seconds()
        if interval >= 3600:
            schedule_str = f"每 {interval/3600:.0f} 小時"
        elif interval >= 60:
            schedule_str = f"每 {interval/60:.0f} 分鐘"
        else:
            schedule_str = f"每 {interval:.0f} 秒"
    else:
        schedule_str = str(schedule)
    
    print(f"  ✓ {task_name}")
    print(f"    任務: {task}")
    print(f"    頻率: {schedule_str}")
    print()
PYTHON_SCRIPT
echo ""

# 總結
echo "=========================================="
echo -e "${GREEN}  ✅ 檢查完成${NC}"
echo "=========================================="
echo ""
echo "📊 檢查摘要："
echo "  1. Docker 容器狀態 - 已檢查"
echo "  2. API 健康狀態 - 已檢查"
echo "  3. 資料庫狀態 - 已檢查"
echo "  4. Celery Beat 調度 - 已檢查"
echo "  5. Celery Worker 執行 - 已檢查"
echo "  6. 手動觸發測試 - 已檢查"
echo "  7. 定時任務配置 - 已檢查"
echo ""
echo "💡 建議："
echo "  - 如果沒有監控事件，請等待 5 分鐘後再次執行此腳本"
echo "  - 如果沒有網域或 DNS 伺服器，請先新增測試資料"
echo "  - 查看完整日誌: docker-compose logs -f celery-worker"
echo ""

