#!/bin/bash

# 驗證修改後的執行狀況
# 用途：確認告警邏輯修正是否生效

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
echo "  🔍 驗證告警邏輯修正"
echo "=========================================="
echo ""

# 步驟 1: 檢查服務狀態
echo -e "${BLUE}[步驟 1]${NC} 檢查服務狀態..."
echo "----------------------------------------"
docker-compose ps | grep -E "dms-api|dms-celery-worker|dms-celery-beat"
echo ""

# 步驟 2: 檢查 API 是否正常
echo -e "${BLUE}[步驟 2]${NC} 檢查 API 健康狀態..."
echo "----------------------------------------"
HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null || echo "")
if [ -n "$HEALTH" ]; then
    echo -e "${GREEN}✅ API 服務正常${NC}"
else
    echo -e "${RED}❌ API 服務異常，請重啟服務${NC}"
    echo "執行: docker-compose restart api celery-worker celery-beat"
    exit 1
fi
echo ""

# 步驟 3: 查看最近的 Worker 日誌
echo -e "${BLUE}[步驟 3]${NC} 查看最近的 Worker 執行日誌..."
echo "----------------------------------------"
echo "最近 10 筆檢查記錄："
docker-compose logs --tail=10 celery-worker | grep -E "Checked domain|succeeded" || echo "⚠️  未找到檢查記錄"
echo ""

# 步驟 4: 統計告警數量
echo -e "${BLUE}[步驟 4]${NC} 統計告警數量..."
echo "----------------------------------------"
docker-compose exec -T api python3 << 'PYTHON_SCRIPT'
from app.database import SessionLocal
from app.models import Alert
from datetime import datetime, timedelta

db = SessionLocal()

# 統計未解決的告警
total_alerts = db.query(Alert).filter(Alert.is_resolved == False).count()
p0_alerts = db.query(Alert).filter(Alert.is_resolved == False, Alert.alert_level == 'P0').count()
p1_alerts = db.query(Alert).filter(Alert.is_resolved == False, Alert.alert_level == 'P1').count()
p2_alerts = db.query(Alert).filter(Alert.is_resolved == False, Alert.alert_level == 'P2').count()

# 統計最近 10 分鐘的新告警
recent_time = datetime.utcnow() - timedelta(minutes=10)
recent_alerts = db.query(Alert).filter(
    Alert.first_seen >= recent_time
).count()

print(f"📊 告警統計：")
print(f"  - 未解決告警總數: {total_alerts}")
print(f"  - P0 (Critical): {p0_alerts}")
print(f"  - P1 (High): {p1_alerts}")
print(f"  - P2 (Normal): {p2_alerts}")
print(f"  - 最近 10 分鐘新增: {recent_alerts}")
print()

# 統計 config_error 告警
config_errors = db.query(Alert).filter(
    Alert.is_resolved == False,
    Alert.root_cause == 'config_error'
).count()

print(f"🔍 config_error 告警數: {config_errors}")
print()

# 顯示最近的告警
print("📋 最近 5 筆告警：")
recent = db.query(Alert).order_by(Alert.last_seen.desc()).limit(5).all()
for a in recent:
    from app.models import Domain
    domain = db.query(Domain).filter(Domain.id == a.domain_id).first()
    domain_name = domain.domain if domain else "Unknown"
    status = "❌ 未解決" if not a.is_resolved else "✅ 已解決"
    print(f"  [{a.alert_level}] {domain_name} - {a.root_cause} {status}")
    print(f"      最後發現: {a.last_seen}")

db.close()
PYTHON_SCRIPT
echo ""

# 步驟 5: 檢查最近的監控事件
echo -e "${BLUE}[步驟 5]${NC} 檢查最近的監控事件..."
echo "----------------------------------------"
docker-compose exec -T api python3 << 'PYTHON_SCRIPT'
from app.database import SessionLocal
from app.models import MonitoringEvent
from datetime import datetime, timedelta

db = SessionLocal()

# 統計最近 10 分鐘的事件
recent_time = datetime.utcnow() - timedelta(minutes=10)
recent_events = db.query(MonitoringEvent).filter(
    MonitoringEvent.timestamp >= recent_time,
    MonitoringEvent.event_type == 'dns_check'
).all()

if recent_events:
    print(f"📝 最近 10 分鐘的 DNS 檢查：{len(recent_events)} 筆")
    
    ok_count = sum(1 for e in recent_events if e.status == 'ok')
    warning_count = sum(1 for e in recent_events if e.status == 'warning')
    critical_count = sum(1 for e in recent_events if e.status == 'critical')
    
    print(f"  - ✅ OK: {ok_count}")
    print(f"  - ⚠️  Warning: {warning_count}")
    print(f"  - ❌ Critical: {critical_count}")
    print()
    
    # 顯示 warning 的網域
    if warning_count > 0:
        print("⚠️  Warning 網域範例（前 5 個）：")
        warning_events = [e for e in recent_events if e.status == 'warning'][:5]
        for e in warning_events:
            from app.models import Domain
            domain = db.query(Domain).filter(Domain.id == e.domain_id).first()
            if domain and e.details:
                success_rate = e.details.get('success_rate', 0)
                print(f"  - {domain.domain}: 成功率 {success_rate*100:.1f}%")
else:
    print("⚠️  最近 10 分鐘沒有新的檢查記錄")
    print("   建議：等待 5 分鐘後再次執行此腳本")

db.close()
PYTHON_SCRIPT
echo ""

# 步驟 6: 測試決策引擎
echo -e "${BLUE}[步驟 6]${NC} 測試決策引擎邏輯..."
echo "----------------------------------------"
docker-compose exec -T api python3 << 'PYTHON_SCRIPT'
from app.decision_engine import AlertDecisionEngine

engine = AlertDecisionEngine()

# 測試案例 1: 白名單問題（不應產生告警）
print("🧪 測試案例 1: 白名單問題")
checks1 = {
    'global_dns': {'status': 'fail', 'resolved_ips': []},
    'isp_dns': {
        'failed_isps': [
            {'nameserver': '8.8.8.8', 'resolved_ips': ['1.2.3.4'], 'reason': 'IP not in whitelist'}
        ],
        'success_rate': 0.0,
        'details': {}
    },
    'securitytrails': {'ns_changed': False, 'whois_changed': False},
    'uptime': {'keyword_match': True, 'available': True}
}
result1 = engine.analyze('test1.com', checks1)
if result1 is None:
    print("  ✅ 正確：白名單問題不產生告警")
else:
    print(f"  ❌ 錯誤：產生了 {result1['alert_level']} 告警")

# 測試案例 2: 真正的 DNS 錯誤（應產生 P2 告警）
print("\n🧪 測試案例 2: DNS 配置錯誤")
checks2 = {
    'global_dns': {'status': 'fail', 'resolved_ips': []},
    'isp_dns': {
        'failed_isps': [
            {'nameserver': '8.8.8.8', 'error': 'Could not contact DNS servers'},
            {'nameserver': '1.1.1.1', 'error': 'Could not contact DNS servers'}
        ],
        'success_rate': 0.0,
        'details': {}
    },
    'securitytrails': {'ns_changed': False, 'whois_changed': False},
    'uptime': {'keyword_match': True, 'available': True}
}
result2 = engine.analyze('test2.com', checks2)
if result2 and result2['alert_level'] == 'P2' and result2['root_cause'] == 'config_error':
    print("  ✅ 正確：產生 P2 config_error 告警")
else:
    print(f"  ❌ 錯誤：{result2}")

# 測試案例 3: 部分成功（不應產生告警）
print("\n🧪 測試案例 3: 部分 DNS 成功")
checks3 = {
    'global_dns': {'status': 'ok', 'resolved_ips': []},
    'isp_dns': {
        'failed_isps': [],
        'success_rate': 0.4,  # 40% 成功率
        'details': {}
    },
    'securitytrails': {'ns_changed': False, 'whois_changed': False},
    'uptime': {'keyword_match': True, 'available': True}
}
result3 = engine.analyze('test3.com', checks3)
if result3 is None:
    print("  ✅ 正確：部分成功不產生告警")
else:
    print(f"  ❌ 錯誤：產生了 {result3['alert_level']} 告警")

PYTHON_SCRIPT
echo ""

# 總結
echo "=========================================="
echo -e "${GREEN}  ✅ 驗證完成${NC}"
echo "=========================================="
echo ""
echo "📊 下一步建議："
echo "  1. 如果 config_error 告警數量仍然很高，等待 5-10 分鐘讓系統自動解決舊告警"
echo "  2. 觀察新產生的告警是否都是真正的問題"
echo "  3. 考慮批量更新 0.0.0.0 的網域配置"
echo ""

