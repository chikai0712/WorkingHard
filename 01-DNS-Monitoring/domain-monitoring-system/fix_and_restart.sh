#!/bin/bash

echo "🔧 修正系統邏輯並重啟"
echo "=========================================="

# 1. 重建容器
echo "1️⃣ 重建 API 和 Worker..."
docker-compose build api celery-worker
docker-compose restart api celery-worker celery-beat

echo ""
echo "⏳ 等待服務啟動..."
sleep 8

# 2. 清理重複告警
echo ""
echo "2️⃣ 清理重複告警..."
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring << 'EOF'
-- 保留每個 domain_id + root_cause 組合中最新的未解決告警,解決其他的
WITH ranked_alerts AS (
    SELECT 
        id,
        ROW_NUMBER() OVER (
            PARTITION BY domain_id, root_cause, is_resolved 
            ORDER BY last_seen DESC
        ) as rn
    FROM alerts
    WHERE is_resolved = false
)
UPDATE alerts
SET is_resolved = true, resolved_at = NOW()
WHERE id IN (
    SELECT id FROM ranked_alerts WHERE rn > 1
);
EOF

echo ""
echo "3️⃣ 統計清理結果:"
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring -c "
SELECT 
    COUNT(*) as total_alerts,
    COUNT(*) FILTER (WHERE is_resolved = false) as unresolved,
    COUNT(*) FILTER (WHERE is_resolved = true) as resolved
FROM alerts;
"

echo ""
echo "=========================================="
echo "✅ 修正完成!"
echo "=========================================="
echo ""
echo "現在執行診斷腳本確認:"
echo "  ./diagnose.sh"
echo ""

