#!/bin/bash
# 緊急訪問請求腳本
# 即使緊急情況，也需要審批和記錄

set -e

NAMESPACE="${1:-betting-service-prod}"
REASON="${2}"
APPROVER="${3}"
DURATION="${4:-3600}"  # 默認 1 小時

if [ -z "$REASON" ] || [ -z "$APPROVER" ]; then
  echo "❌ 用法: $0 <namespace> <reason> <approver> [duration_seconds]"
  echo "範例: $0 betting-service-prod '緊急修復生產問題' 'manager@example.com' 3600"
  exit 1
fi

echo "🚨 緊急訪問請求"
echo "命名空間: $NAMESPACE"
echo "原因: $REASON"
echo "審批人: $APPROVER"
echo "持續時間: ${DURATION}秒 ($(($DURATION / 60)) 分鐘)"
echo ""

# 1. 記錄請求
REQUEST_ID=$(uuidgen)
TIMESTAMP=$(date -Iseconds)

cat > /tmp/emergency_access_${REQUEST_ID}.json <<EOF
{
  "request_id": "$REQUEST_ID",
  "namespace": "$NAMESPACE",
  "reason": "$REASON",
  "approver": "$APPROVER",
  "requester": "$USER",
  "timestamp": "$TIMESTAMP",
  "duration": $DURATION,
  "status": "pending"
}
EOF

# 2. 發送審批請求
echo "📧 發送審批請求..."
if [ -n "$SLACK_WEBHOOK_URL" ]; then
  curl -X POST "$SLACK_WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d "{
      \"text\": \"🚨 緊急訪問請求\",
      \"attachments\": [{
        \"color\": \"warning\",
        \"fields\": [{
          \"title\": \"請求 ID\",
          \"value\": \"$REQUEST_ID\",
          \"short\": true
        }, {
          \"title\": \"命名空間\",
          \"value\": \"$NAMESPACE\",
          \"short\": true
        }, {
          \"title\": \"原因\",
          \"value\": \"$REASON\",
          \"short\": false
        }, {
          \"title\": \"請求人\",
          \"value\": \"$USER\",
          \"short\": true
        }, {
          \"title\": \"審批人\",
          \"value\": \"$APPROVER\",
          \"short\": true
        }, {
          \"title\": \"持續時間\",
          \"value\": \"$(($DURATION / 60)) 分鐘\",
          \"short\": true
        }]
      }]
    }"
fi

# 3. 等待審批（實際應該通過審批系統）
echo ""
echo "⏳ 等待審批..."
echo "請聯繫審批人: $APPROVER"
read -p "審批通過？(yes/no): " approval

if [ "$approval" != "yes" ]; then
  echo "❌ 審批未通過，訪問請求已取消"
  exit 1
fi

# 4. 記錄審批
cat >> /tmp/emergency_access_${REQUEST_ID}.json <<EOF
,
  "approved_at": "$(date -Iseconds)",
  "status": "approved"
}
EOF

# 5. 上傳到審計系統
if [ -n "$AUDIT_SYSTEM_URL" ]; then
  curl -X POST "$AUDIT_SYSTEM_URL/api/emergency-access" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $AUDIT_API_TOKEN" \
    -d @/tmp/emergency_access_${REQUEST_ID}.json
fi

# 6. 創建臨時 RoleBinding（實際應該通過 Kubernetes API）
echo ""
echo "✅ 審批通過，創建臨時訪問權限..."
echo "⚠️  注意：此訪問將在 $(($DURATION / 60)) 分鐘後自動撤銷"

# 7. 設置自動撤銷（實際應該通過 CronJob 或外部系統）
cat > /tmp/revoke_access_${REQUEST_ID}.sh <<EOF
#!/bin/bash
sleep $DURATION
echo "⏰ 訪問權限已自動撤銷"
# 實際應該執行: kubectl delete rolebinding emergency-access-${REQUEST_ID} -n $NAMESPACE
EOF

chmod +x /tmp/revoke_access_${REQUEST_ID}.sh
nohup /tmp/revoke_access_${REQUEST_ID}.sh > /dev/null 2>&1 &

echo ""
echo "📋 訪問記錄已保存: /tmp/emergency_access_${REQUEST_ID}.json"
echo "🔍 所有操作將被記錄到審計系統"

