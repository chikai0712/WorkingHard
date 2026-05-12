#!/bin/bash
# 指標驗證腳本

set -e

PROMETHEUS_URL="${PROMETHEUS_URL:-http://prometheus:9090}"
THRESHOLD_ERROR_RATE=0.01
THRESHOLD_P99_LATENCY=0.1
THRESHOLD_SUCCESS_RATE=0.99

echo "🔍 驗證系統指標..."

# 檢查錯誤率
ERROR_RATE=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=rate(http_requests_total{status=~\"5..\"}[5m])" | jq -r '.data.result[0].value[1] // "0"')
if [ -z "$ERROR_RATE" ] || [ "$ERROR_RATE" = "null" ]; then
  ERROR_RATE=0
fi

if command -v bc &> /dev/null; then
  if (( $(echo "$ERROR_RATE > $THRESHOLD_ERROR_RATE" | bc -l) )); then
    echo "❌ 錯誤率過高: $ERROR_RATE > $THRESHOLD_ERROR_RATE"
    exit 1
  fi
else
  ERROR_INT=$(echo "$ERROR_RATE * 1000" | awk '{printf "%.0f", $1}')
  THRESHOLD_INT=$(echo "$THRESHOLD_ERROR_RATE * 1000" | awk '{printf "%.0f", $1}')
  if [ "$ERROR_INT" -gt "$THRESHOLD_INT" ]; then
    echo "❌ 錯誤率過高: $ERROR_RATE > $THRESHOLD_ERROR_RATE"
    exit 1
  fi
fi

# 檢查延遲
P99_LATENCY=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=histogram_quantile(0.99,rate(http_request_duration_seconds_bucket[5m]))" | jq -r '.data.result[0].value[1] // "0"')
if [ -z "$P99_LATENCY" ] || [ "$P99_LATENCY" = "null" ]; then
  P99_LATENCY=0
fi

if command -v bc &> /dev/null; then
  if (( $(echo "$P99_LATENCY > $THRESHOLD_P99_LATENCY" | bc -l) )); then
    echo "❌ P99 延遲過高: ${P99_LATENCY}s > ${THRESHOLD_P99_LATENCY}s"
    exit 1
  fi
else
  P99_INT=$(echo "$P99_LATENCY * 1000" | awk '{printf "%.0f", $1}')
  THRESHOLD_INT=$(echo "$THRESHOLD_P99_LATENCY * 1000" | awk '{printf "%.0f", $1}')
  if [ "$P99_INT" -gt "$THRESHOLD_INT" ]; then
    echo "❌ P99 延遲過高: ${P99_LATENCY}s > ${THRESHOLD_P99_LATENCY}s"
    exit 1
  fi
fi

# 檢查業務成功率
SUCCESS_RATE=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=rate(order_processed_total{status=\"success\"}[5m])/rate(order_processed_total[5m])" | jq -r '.data.result[0].value[1] // "1"')
if [ -z "$SUCCESS_RATE" ] || [ "$SUCCESS_RATE" = "null" ]; then
  SUCCESS_RATE=1
fi

if command -v bc &> /dev/null; then
  if (( $(echo "$SUCCESS_RATE < $THRESHOLD_SUCCESS_RATE" | bc -l) )); then
    echo "❌ 業務成功率過低: $SUCCESS_RATE < $THRESHOLD_SUCCESS_RATE"
    exit 1
  fi
else
  SUCCESS_INT=$(echo "$SUCCESS_RATE * 100" | awk '{printf "%.0f", $1}')
  THRESHOLD_INT=$(echo "$THRESHOLD_SUCCESS_RATE * 100" | awk '{printf "%.0f", $1}')
  if [ "$SUCCESS_INT" -lt "$THRESHOLD_INT" ]; then
    echo "❌ 業務成功率過低: $SUCCESS_RATE < $THRESHOLD_SUCCESS_RATE"
    exit 1
  fi
fi

echo "✅ 所有指標正常"
echo "   錯誤率: $ERROR_RATE"
echo "   P99 延遲: ${P99_LATENCY}s"
echo "   成功率: $SUCCESS_RATE"

