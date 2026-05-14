#!/bin/bash

# 手動測試特定網域的 DNS 解析
# 用途：驗證告警是否正確

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DOMAIN1="ppllddhc.com"
DOMAIN2="winplay.co.za"

echo "=========================================="
echo "  🔍 手動測試網域 DNS 解析"
echo "=========================================="
echo ""

# 測試函數
test_domain() {
    local domain=$1
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}測試網域: ${domain}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # 1. 使用系統 DNS 查詢
    echo "📍 [1] 使用系統 DNS 查詢："
    if dig +short $domain A | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' > /dev/null 2>&1; then
        IPS=$(dig +short $domain A)
        echo -e "${GREEN}✅ 解析成功${NC}"
        echo "   IP 地址: $IPS"
    else
        echo -e "${RED}❌ 解析失敗${NC}"
    fi
    echo ""
    
    # 2. 使用 Google DNS (8.8.8.8)
    echo "📍 [2] 使用 Google DNS (8.8.8.8)："
    if dig @8.8.8.8 +short $domain A | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' > /dev/null 2>&1; then
        IPS=$(dig @8.8.8.8 +short $domain A)
        echo -e "${GREEN}✅ 解析成功${NC}"
        echo "   IP 地址: $IPS"
    else
        echo -e "${RED}❌ 解析失敗${NC}"
    fi
    echo ""
    
    # 3. 使用 Cloudflare DNS (1.1.1.1)
    echo "📍 [3] 使用 Cloudflare DNS (1.1.1.1)："
    if dig @1.1.1.1 +short $domain A | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' > /dev/null 2>&1; then
        IPS=$(dig @1.1.1.1 +short $domain A)
        echo -e "${GREEN}✅ 解析成功${NC}"
        echo "   IP 地址: $IPS"
    else
        echo -e "${RED}❌ 解析失敗${NC}"
    fi
    echo ""
    
    # 4. 使用中華電信 DNS (168.95.1.1)
    echo "📍 [4] 使用中華電信 DNS (168.95.1.1)："
    if dig @168.95.1.1 +short $domain A | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' > /dev/null 2>&1; then
        IPS=$(dig @168.95.1.1 +short $domain A)
        echo -e "${GREEN}✅ 解析成功${NC}"
        echo "   IP 地址: $IPS"
    else
        echo -e "${RED}❌ 解析失敗${NC}"
    fi
    echo ""
    
    # 5. 查詢 NS 記錄
    echo "📍 [5] 查詢 NS 記錄："
    NS_RECORDS=$(dig +short $domain NS)
    if [ -n "$NS_RECORDS" ]; then
        echo -e "${GREEN}✅ NS 記錄存在${NC}"
        echo "$NS_RECORDS" | while read ns; do
            echo "   - $ns"
        done
    else
        echo -e "${RED}❌ 無 NS 記錄${NC}"
    fi
    echo ""
    
    # 6. 查詢 WHOIS 資訊
    echo "📍 [6] 查詢 WHOIS 資訊："
    WHOIS_INFO=$(whois $domain 2>/dev/null | grep -i "status\|expir" | head -3)
    if [ -n "$WHOIS_INFO" ]; then
        echo "$WHOIS_INFO"
    else
        echo -e "${YELLOW}⚠️  無法取得 WHOIS 資訊${NC}"
    fi
    echo ""
    
    # 7. 查看系統中的配置
    echo "📍 [7] 查看監控系統配置："
    docker-compose exec -T api python3 << PYTHON_SCRIPT
from app.database import SessionLocal
from app.models import Domain, Alert, MonitoringEvent

db = SessionLocal()

domain = db.query(Domain).filter(Domain.domain == '$domain').first()
if domain:
    print(f"   網域 ID: {domain.id}")
    print(f"   預期 IP: {domain.expected_ips}")
    print(f"   預期 NS: {domain.expected_ns}")
    print(f"   啟用狀態: {'✅ 啟用' if domain.is_active else '❌ 停用'}")
    
    # 查看最近的檢查結果
    recent_event = db.query(MonitoringEvent).filter(
        MonitoringEvent.domain_id == domain.id,
        MonitoringEvent.event_type == 'dns_check'
    ).order_by(MonitoringEvent.timestamp.desc()).first()
    
    if recent_event:
        print(f"   最近檢查: {recent_event.timestamp}")
        print(f"   檢查狀態: {recent_event.status}")
        if recent_event.details:
            success_rate = recent_event.details.get('success_rate', 0)
            print(f"   成功率: {success_rate * 100:.1f}%")
            
            failed_ns = recent_event.details.get('failed_nameservers', [])
            if failed_ns:
                print(f"   失敗的 DNS 伺服器:")
                for ns in failed_ns[:3]:
                    error = ns.get('error', ns.get('reason', 'Unknown'))
                    print(f"     - {ns.get('nameserver')}: {error}")
    
    # 查看告警
    alert = db.query(Alert).filter(
        Alert.domain_id == domain.id,
        Alert.is_resolved == False
    ).first()
    
    if alert:
        print(f"   告警等級: {alert.alert_level}")
        print(f"   根因: {alert.root_cause}")
        print(f"   首次發現: {alert.first_seen}")
        print(f"   最後發現: {alert.last_seen}")
else:
    print(f"   ❌ 網域不在監控系統中")

db.close()
PYTHON_SCRIPT
    echo ""
    
    # 8. 手動觸發檢查
    echo "📍 [8] 手動觸發系統檢查："
    RESULT=$(curl -s -X POST http://localhost:8000/api/check/dns \
      -H "Content-Type: application/json" \
      -d "{\"domain\": \"$domain\"}" 2>/dev/null)
    
    if [ -n "$RESULT" ]; then
        echo "$RESULT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('status') == 'success':
        results = data.get('results', {})
        success_rate = results.get('success_rate', 0)
        print(f'   檢查狀態: ✅ 成功')
        print(f'   成功率: {success_rate * 100:.1f}%')
        print(f'   檢查的 DNS 數量: {results.get(\"total_checks\", 0)}')
        print(f'   成功數量: {results.get(\"success_count\", 0)}')
        
        if success_rate == 0:
            print('   ❌ 所有 DNS 伺服器都無法解析')
        elif success_rate < 0.5:
            print('   ⚠️  部分 DNS 伺服器無法解析')
        else:
            print('   ✅ 大部分 DNS 伺服器解析成功')
    else:
        print(f'   ❌ 檢查失敗: {data.get(\"detail\", \"Unknown error\")}')
except:
    print('   ❌ 無法解析回應')
"
    else
        echo -e "   ${RED}❌ API 請求失敗${NC}"
    fi
    echo ""
}

# 測試兩個網域
test_domain $DOMAIN1
echo ""
test_domain $DOMAIN2

# 總結
echo "=========================================="
echo -e "${GREEN}  ✅ 測試完成${NC}"
echo "=========================================="
echo ""
echo "📊 判斷標準："
echo "  ✅ 如果所有 DNS 都無法解析 → P2 告警正確"
echo "  ⚠️  如果部分 DNS 可以解析 → 可能是白名單問題"
echo "  ❌ 如果所有 DNS 都能解析 → 告警錯誤，需要調查"
echo ""

