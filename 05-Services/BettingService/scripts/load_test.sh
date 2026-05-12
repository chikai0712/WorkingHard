#!/bin/bash

# 壓力測試腳本
# 使用 Apache Bench (ab) 或 wrk

GATEWAY_URL="http://localhost:8080"
CONCURRENT=1000
REQUESTS=100000

echo "開始壓力測試..."
echo "Gateway URL: $GATEWAY_URL"
echo "並發數: $CONCURRENT"
echo "總請求數: $REQUESTS"
echo ""

# 檢查是否安裝了 wrk
if command -v wrk &> /dev/null; then
    echo "使用 wrk 進行測試..."
    wrk -t12 -c${CONCURRENT} -d30s --timeout 10s \
        -s test_script.lua \
        ${GATEWAY_URL}/api/v1/orders
elif command -v ab &> /dev/null; then
    echo "使用 Apache Bench 進行測試..."
    ab -n ${REQUESTS} -c ${CONCURRENT} \
        -p test_order.json \
        -T application/json \
        ${GATEWAY_URL}/api/v1/orders
else
    echo "請安裝 wrk 或 Apache Bench (ab)"
    exit 1
fi

