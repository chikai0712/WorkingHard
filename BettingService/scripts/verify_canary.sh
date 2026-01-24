#!/bin/bash
# 金絲雀部署驗證腳本

set -e

NAMESPACE="${K8S_NAMESPACE:-betting-service}"
CANARY_DEPLOYMENT="order-service-canary"
TIMEOUT=600  # 10 分鐘
PROMETHEUS_URL="${PROMETHEUS_URL:-http://prometheus:9090}"

echo "🔍 開始驗證金絲雀部署..."

# 1. 檢查 Pod 是否就緒
echo "1. 檢查 Pod 狀態..."
if ! kubectl wait --for=condition=ready pod -l version=canary -n $NAMESPACE --timeout=${TIMEOUT}s; then
  echo "❌ Pod 未就緒"
  exit 1
fi

# 2. 檢查健康檢查端點
echo "2. 檢查健康檢查端點..."
CANARY_POD=$(kubectl get pod -l version=canary -n $NAMESPACE -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -z "$CANARY_POD" ]; then
  echo "❌ 未找到 Canary Pod"
  exit 1
fi

if ! kubectl exec -n $NAMESPACE $CANARY_POD -- curl -f http://localhost:8080/health > /dev/null 2>&1; then
  echo "❌ 健康檢查失敗"
  exit 1
fi

# 3. 檢查錯誤率（從 Prometheus）
echo "3. 檢查錯誤率..."
sleep 30  # 等待指標收集

ERROR_RATE=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=rate(http_requests_total{version=\"canary\",status=~\"5..\"}[5m])" | jq -r '.data.result[0].value[1] // "0"')
if [ -z "$ERROR_RATE" ] || [ "$ERROR_RATE" = "null" ]; then
  ERROR_RATE=0
fi

# 使用 awk 進行浮點數比較（如果 bc 不可用）
if command -v bc &> /dev/null; then
  if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
    echo "❌ 錯誤率過高: $ERROR_RATE"
    exit 1
  fi
else
  # 簡單的字符串比較（適用於小數）
  ERROR_INT=$(echo "$ERROR_RATE * 1000" | awk '{printf "%.0f", $1}')
  if [ "$ERROR_INT" -gt 10 ]; then
    echo "❌ 錯誤率過高: $ERROR_RATE"
    exit 1
  fi
fi

# 4. 檢查延遲（P99）
echo "4. 檢查延遲..."
P99_LATENCY=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=histogram_quantile(0.99,rate(http_request_duration_seconds_bucket{version=\"canary\"}[5m]))" | jq -r '.data.result[0].value[1] // "0"')
if [ -z "$P99_LATENCY" ] || [ "$P99_LATENCY" = "null" ]; then
  P99_LATENCY=0
fi

if command -v bc &> /dev/null; then
  if (( $(echo "$P99_LATENCY > 0.1" | bc -l) )); then
    echo "❌ P99 延遲過高: ${P99_LATENCY}s"
    exit 1
  fi
else
  P99_INT=$(echo "$P99_LATENCY * 1000" | awk '{printf "%.0f", $1}')
  if [ "$P99_INT" -gt 100 ]; then
    echo "❌ P99 延遲過高: ${P99_LATENCY}s"
    exit 1
  fi
fi

# 5. 檢查業務指標（注單處理成功率）
echo "5. 檢查業務指標..."
SUCCESS_RATE=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=rate(order_processed_total{version=\"canary\",status=\"success\"}[5m])/rate(order_processed_total{version=\"canary\"}[5m])" | jq -r '.data.result[0].value[1] // "1"')
if [ -z "$SUCCESS_RATE" ] || [ "$SUCCESS_RATE" = "null" ]; then
  SUCCESS_RATE=1
fi

if command -v bc &> /dev/null; then
  if (( $(echo "$SUCCESS_RATE < 0.99" | bc -l) )); then
    echo "❌ 注單處理成功率過低: $SUCCESS_RATE"
    exit 1
  fi
else
  SUCCESS_INT=$(echo "$SUCCESS_RATE * 100" | awk '{printf "%.0f", $1}')
  if [ "$SUCCESS_INT" -lt 99 ]; then
    echo "❌ 注單處理成功率過低: $SUCCESS_RATE"
    exit 1
  fi
fi

echo "✅ 金絲雀驗證通過！"
echo "   錯誤率: $ERROR_RATE"
echo "   P99 延遲: ${P99_LATENCY}s"
echo "   成功率: $SUCCESS_RATE"

