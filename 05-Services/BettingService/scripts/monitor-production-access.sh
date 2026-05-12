#!/bin/bash
# 監控生產環境訪問腳本
# 檢測異常訪問行為

set -e

NAMESPACE="${1:-betting-service-prod}"
ALERT_THRESHOLD=5  # 5 分鐘內超過此數量的操作視為異常

echo "🔍 監控生產環境訪問..."
echo "命名空間: $NAMESPACE"
echo ""

# 1. 檢查最近的 kubectl 操作
echo "📊 最近的 kubectl 操作:"
kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -20

# 2. 檢查異常的 Pod 執行操作
echo ""
echo "⚠️  檢查 Pod 執行操作:"
EXEC_OPERATIONS=$(kubectl get events -n $NAMESPACE --field-selector reason=Exec | wc -l)
if [ "$EXEC_OPERATIONS" -gt 0 ]; then
  echo "❌ 發現 $EXEC_OPERATIONS 個 Pod 執行操作"
  kubectl get events -n $NAMESPACE --field-selector reason=Exec
fi

# 3. 檢查異常的配置變更
echo ""
echo "⚠️  檢查配置變更:"
RECENT_CHANGES=$(kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | grep -i "update\|create\|delete" | tail -10)
if [ -n "$RECENT_CHANGES" ]; then
  echo "發現最近的配置變更:"
  echo "$RECENT_CHANGES"
fi

# 4. 檢查 ServiceAccount 使用情況
echo ""
echo "👤 ServiceAccount 使用情況:"
kubectl get serviceaccounts -n $NAMESPACE
kubectl get rolebindings -n $NAMESPACE
kubectl get clusterrolebindings | grep -i "$NAMESPACE\|betting"

# 5. 檢查審計日誌（如果啟用）
echo ""
echo "📋 審計日誌摘要:"
if kubectl get events -n $NAMESPACE --field-selector type=Warning 2>/dev/null | grep -q .; then
  echo "⚠️  發現警告事件:"
  kubectl get events -n $NAMESPACE --field-selector type=Warning | tail -10
fi

# 6. 生成報告
REPORT_FILE="production_access_report_$(date +%Y%m%d_%H%M%S).txt"
{
  echo "=== 生產環境訪問監控報告 ==="
  echo "時間: $(date)"
  echo "命名空間: $NAMESPACE"
  echo ""
  echo "Pod 執行操作: $EXEC_OPERATIONS"
  echo ""
  echo "最近的配置變更:"
  echo "$RECENT_CHANGES"
} > $REPORT_FILE

echo ""
echo "✅ 報告已生成: $REPORT_FILE"

# 7. 發送告警（如果發現異常）
if [ "$EXEC_OPERATIONS" -gt "$ALERT_THRESHOLD" ]; then
  echo "🚨 發現異常訪問行為，發送告警..."
  if [ -n "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST "$SLACK_WEBHOOK_URL" \
      -H "Content-Type: application/json" \
      -d "{
        \"text\": \"🚨 生產環境異常訪問告警\",
        \"attachments\": [{
          \"color\": \"danger\",
          \"fields\": [{
            \"title\": \"命名空間\",
            \"value\": \"$NAMESPACE\",
            \"short\": true
          }, {
            \"title\": \"Pod 執行操作數\",
            \"value\": \"$EXEC_OPERATIONS\",
            \"short\": true
          }]
        }]
      }"
  fi
fi

