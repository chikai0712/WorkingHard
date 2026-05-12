#!/bin/bash

# 快速檢查域名狀態

echo "🔍 檢查域名狀態"
echo "=========================================="

# 1. 統計域名狀態
echo "📊 域名統計:"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c "
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE is_active = true) as active,
    COUNT(*) FILTER (WHERE is_active = false) as inactive,
    COUNT(*) FILTER (WHERE '0.0.0.0' = ANY(expected_ips)) as failed_dns
FROM domains;
"

echo ""
echo "📋 無法解析的域名 (前 10 個):"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c "
SELECT domain, is_active 
FROM domains 
WHERE '0.0.0.0' = ANY(expected_ips)
LIMIT 10;
"

echo ""
echo "✅ 正常解析的域名 (前 10 個):"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c "
SELECT domain, expected_ips 
FROM domains 
WHERE NOT ('0.0.0.0' = ANY(expected_ips))
AND is_active = true
LIMIT 10;
"

echo ""
echo "🔔 告警統計:"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c "
SELECT 
    COUNT(*) as total_alerts,
    COUNT(*) FILTER (WHERE is_resolved = false) as unresolved,
    COUNT(*) FILTER (WHERE alert_level = 'P0') as p0,
    COUNT(*) FILTER (WHERE alert_level = 'P1') as p1,
    COUNT(*) FILTER (WHERE alert_level = 'P2') as p2
FROM alerts;
"

echo ""
echo "=========================================="

