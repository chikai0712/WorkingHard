#!/bin/bash

echo "🔍 詳細診斷域名狀態"
echo "=========================================="

# 1. 檢查有多少域名的 IP 是 0.0.0.0
echo "📊 1. 檢查 expected_ips 狀態:"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c "
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE '0.0.0.0' = ANY(expected_ips)) as has_zero_ip,
    COUNT(*) FILTER (WHERE array_length(expected_ips, 1) > 0 AND NOT ('0.0.0.0' = ANY(expected_ips))) as has_valid_ip
FROM domains;
"

echo ""
echo "📋 2. 隨機抽樣 10 個域名的 IP:"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c "
SELECT domain, expected_ips, is_active 
FROM domains 
ORDER BY RANDOM()
LIMIT 10;
"

echo ""
echo "🔔 3. 最近的告警原因分布:"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c "
SELECT 
    root_cause,
    COUNT(*) as count,
    COUNT(*) FILTER (WHERE is_resolved = false) as unresolved
FROM alerts 
GROUP BY root_cause
ORDER BY count DESC;
"

echo ""
echo "📊 4. 最近的監控事件狀態:"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c "
SELECT 
    status,
    COUNT(*) as count
FROM monitoring_events 
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY status
ORDER BY count DESC;
"

echo ""
echo "🔍 5. 隨機檢查 5 個域名的最新監控結果:"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c "
SELECT 
    d.domain,
    d.expected_ips,
    me.status,
    me.details->>'success_rate' as success_rate,
    me.timestamp
FROM monitoring_events me
JOIN domains d ON d.id = me.domain_id
WHERE me.timestamp > NOW() - INTERVAL '10 minutes'
ORDER BY me.timestamp DESC
LIMIT 5;
"

echo ""
echo "=========================================="

