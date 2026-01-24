#!/bin/bash
# 回滾腳本

set -e

NAMESPACE="${K8S_NAMESPACE:-betting-service}"

echo "🔄 開始回滾..."

# 檢查是否使用 Istio
if kubectl get virtualservice order-service -n $NAMESPACE &>/dev/null; then
  USE_ISTIO=true
elif kubectl get ingress order-service-canary -n $NAMESPACE &>/dev/null; then
  USE_ISTIO=false
else
  USE_ISTIO=false
fi

# 1. 將流量切回 Production
echo "1. 將流量切回 Production..."
if [ "$USE_ISTIO" = true ]; then
  kubectl patch virtualservice order-service -n $NAMESPACE --type=json -p='
  [
    {"op": "replace", "path": "/spec/http/1/route/0/weight", "value": 0},
    {"op": "replace", "path": "/spec/http/1/route/1/weight", "value": 100}
  ]'
else
  kubectl patch ingress order-service-canary -n $NAMESPACE --type=json -p='
  [
    {"op": "replace", "path": "/metadata/annotations/nginx.ingress.kubernetes.io~1canary-weight", "value": "0"}
  ]'
fi

# 2. 縮容 Canary Deployment
echo "2. 縮容 Canary Deployment..."
kubectl scale deployment order-service-canary --replicas=0 -n $NAMESPACE

# 3. 回滾 Production Deployment（如果已更新）
echo "3. 回滾 Production Deployment..."
if kubectl rollout history deployment/order-service-production -n $NAMESPACE | grep -q "revision"; then
  kubectl rollout undo deployment/order-service-production -n $NAMESPACE
  kubectl rollout status deployment/order-service-production -n $NAMESPACE --timeout=5m
else
  echo "⚠️  無歷史版本可回滾"
fi

echo "✅ 回滾完成"

