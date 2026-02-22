#!/bin/bash

# 域名檢測邏輯驗證腳本

echo "🔍 域名檢測邏輯驗證"
echo "=========================================="

# 選擇幾個測試域名
TEST_DOMAINS=(
    "wewa88.com"           # 應該正常
    "bet-brazil.com"       # 無法解析
    "crownjem.com"         # 應該正常
    "ppllddhc.com"         # 無法解析
    "sbclive88.org"        # 應該正常
)

echo "測試域名列表:"
for domain in "${TEST_DOMAINS[@]}"; do
    echo "  - $domain"
done
echo ""

# 1. 使用 dig 測試 DNS 解析
echo "1️⃣ 使用 dig 測試 DNS 解析 (Google DNS 8.8.8.8)"
echo "----------------------------------------"
for domain in "${TEST_DOMAINS[@]}"; do
    echo -n "測試 $domain ... "
    result=$(dig @8.8.8.8 +short $domain A 2>/dev/null)
    if [ -z "$result" ]; then
        echo "❌ 無法解析"
    else
        echo "✅ $result"
    fi
done

echo ""
echo "2️⃣ 檢查資料庫中的域名配置"
echo "----------------------------------------"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring << 'EOF'
SELECT 
    domain,
    expected_ips,
    is_active,
    CASE 
        WHEN '0.0.0.0' = ANY(expected_ips) THEN '❌ IP 未設定'
        ELSE '✅ IP 已設定'
    END as ip_status
FROM domains 
WHERE domain IN ('wewa88.com', 'bet-brazil.com', 'crownjem.com', 'ppllddhc.com', 'sbclive88.org')
ORDER BY domain;
EOF

echo ""
echo "3️⃣ 檢查最近的監控事件"
echo "----------------------------------------"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring << 'EOF'
SELECT 
    d.domain,
    me.status,
    me.details->>'success_rate' as success_rate,
    TO_CHAR(me.timestamp, 'HH24:MI:SS') as time
FROM monitoring_events me
JOIN domains d ON d.id = me.domain_id
WHERE d.domain IN ('wewa88.com', 'bet-brazil.com', 'crownjem.com', 'ppllddhc.com', 'sbclive88.org')
AND me.timestamp > NOW() - INTERVAL '30 minutes'
ORDER BY me.timestamp DESC
LIMIT 10;
EOF

echo ""
echo "4️⃣ 檢查告警狀態"
echo "----------------------------------------"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring << 'EOF'
SELECT 
    d.domain,
    a.alert_level,
    a.root_cause,
    a.is_resolved,
    TO_CHAR(a.last_seen, 'HH24:MI:SS') as last_seen
FROM alerts a
JOIN domains d ON d.id = a.domain_id
WHERE d.domain IN ('wewa88.com', 'bet-brazil.com', 'crownjem.com', 'ppllddhc.com', 'sbclive88.org')
AND a.is_resolved = false
ORDER BY a.last_seen DESC;
EOF

echo ""
echo "5️⃣ 測試 Python DNS 解析 (與系統相同的方法)"
echo "----------------------------------------"
docker exec -i dms-api python3 << 'PYEOF'
import asyncio
import aiodns

async def test_dns(domain):
    resolver = aiodns.DNSResolver(nameservers=["8.8.8.8"], timeout=5)
    try:
        result = await resolver.query(domain, 'A')
        ips = [r.host for r in result]
        print(f"✅ {domain}: {', '.join(ips)}")
        return True
    except Exception as e:
        print(f"❌ {domain}: {e}")
        return False

async def main():
    domains = ['wewa88.com', 'bet-brazil.com', 'crownjem.com', 'ppllddhc.com', 'sbclive88.org']
    for domain in domains:
        await test_dns(domain)

asyncio.run(main())
PYEOF

echo ""
echo "6️⃣ 檢查 DNS 檢查邏輯"
echo "----------------------------------------"
echo "檢查條件:"
echo "  - success_rate > 0.8 → 狀態: ok"
echo "  - success_rate <= 0.8 → 狀態: warning"
echo "  - 使用 5 個 DNS 伺服器檢查"
echo "  - IP 必須在 expected_ips 白名單中"
echo ""

docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c "
SELECT dns_server, isp_name, is_healthy 
FROM nameservers 
ORDER BY id;
"

echo ""
echo "7️⃣ 分析檢測邏輯問題"
echo "----------------------------------------"

# 統計正常和異常的域名
NORMAL_COUNT=$(docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -t -c "
SELECT COUNT(*) 
FROM domains 
WHERE is_active = true 
AND NOT ('0.0.0.0' = ANY(expected_ips));
" | tr -d ' ')

FAILED_COUNT=$(docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -t -c "
SELECT COUNT(*) 
FROM domains 
WHERE is_active = true 
AND '0.0.0.0' = ANY(expected_ips);
" | tr -d ' ')

echo "域名統計:"
echo "  ✅ 正常域名 (IP 已設定): $NORMAL_COUNT 個"
echo "  ❌ 異常域名 (IP 未設定): $FAILED_COUNT 個"
echo ""

# 檢查最近的監控成功率
echo "最近 1 小時監控成功率:"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -t -c "
SELECT 
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM monitoring_events 
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY status;
"

echo ""
echo "=========================================="
echo "📋 結論"
echo "=========================================="
echo ""
echo "如果發現問題:"
echo "1. IP 未設定 (0.0.0.0) → 執行: docker exec -i dms-api python update_domain_ips.py"
echo "2. DNS 伺服器不健康 → 檢查 nameservers 表"
echo "3. 檢測邏輯錯誤 → 檢查 app/tasks.py 中的 check_single_domain"
echo "4. 白名單不匹配 → 更新 expected_ips"
echo ""

