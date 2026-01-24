#!/bin/bash
# 漸進式流量切換腳本

set -e

VERSION=$1
NAMESPACE="${K8S_NAMESPACE:-betting-service}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://prometheus:9090}"

if [ -z "$VERSION" ]; then
  echo "❌ 請提供版本號"
  exit 1
fi

echo "🚀 開始漸進式部署版本: $VERSION"

# 檢查是否使用 Istio
if kubectl get virtualservice order-service -n $NAMESPACE &>/dev/null; then
  USE_ISTIO=true
  echo "📊 使用 Istio VirtualService 進行流量切割"
elif kubectl get ingress order-service-canary -n $NAMESPACE &>/dev/null; then
  USE_ISTIO=false
  echo "📊 使用 Nginx Ingress 進行流量切割"
else
  echo "⚠️  未找到流量切割配置，使用標準滾動更新"
  kubectl set image deployment/order-service-production order-service=betting-service/order-service:$VERSION -n $NAMESPACE
  kubectl rollout status deployment/order-service-production -n $NAMESPACE --timeout=10m
  exit 0
fi

# 階段 1: 10% 流量（已通過金絲雀驗證）
echo ""
echo "📊 階段 1: 10% 流量到新版本..."
if [ "$USE_ISTIO" = true ]; then
  kubectl patch virtualservice order-service -n $NAMESPACE --type=json -p='
  [
    {"op": "replace", "path": "/spec/http/1/route/0/weight", "value": 10},
    {"op": "replace", "path": "/spec/http/1/route/1/weight", "value": 90}
  ]'
else
  kubectl patch ingress order-service-canary -n $NAMESPACE --type=json -p='
  [
    {"op": "replace", "path": "/metadata/annotations/nginx.ingress.kubernetes.io~1canary-weight", "value": "10"}
  ]'
fi

echo "⏳ 等待 5 分鐘，監控指標..."
sleep 300

if [ -f scripts/verify_metrics.sh ]; then
  chmod +x scripts/verify_metrics.sh
  ./scripts/verify_metrics.sh || {
    echo "❌ 驗證失敗，回滾..."
    ./scripts/rollback.sh
    exit 1
  }
fi

# 階段 2: 50% 流量
echo ""
echo "📊 階段 2: 50% 流量到新版本..."
if [ "$USE_ISTIO" = true ]; then
  kubectl patch virtualservice order-service -n $NAMESPACE --type=json -p='
  [
    {"op": "replace", "path": "/spec/http/1/route/0/weight", "value": 50},
    {"op": "replace", "path": "/spec/http/1/route/1/weight", "value": 50}
  ]'
else
  kubectl patch ingress order-service-canary -n $NAMESPACE --type=json -p='
  [
    {"op": "replace", "path": "/metadata/annotations/nginx.ingress.kubernetes.io~1canary-weight", "value": "50"}
  ]'
fi

echo "⏳ 等待 5 分鐘，監控指標..."
sleep 300

if [ -f scripts/verify_metrics.sh ]; then
  ./scripts/verify_metrics.sh || {
    echo "❌ 驗證失敗，回滾..."
    ./scripts/rollback.sh
    exit 1
  }
fi

# 階段 3: 100% 流量
echo ""
echo "📊 階段 3: 100% 流量到新版本..."
if [ "$USE_ISTIO" = true ]; then
  kubectl patch virtualservice order-service -n $NAMESPACE --type=json -p='
  [
    {"op": "replace", "path": "/spec/http/1/route/0/weight", "value": 100},
    {"op": "replace", "path": "/spec/http/1/route/1/weight", "value": 0}
  ]'
else
  kubectl patch ingress order-service-canary -n $NAMESPACE --type=json -p='
  [
    {"op": "replace", "path": "/metadata/annotations/nginx.ingress.kubernetes.io~1canary-weight", "value": "100"}
  ]'
fi

# 更新 Production Deployment
echo ""
echo "🔄 更新 Production Deployment..."
kubectl set image deployment/order-service-production order-service=betting-service/order-service:$VERSION -n $NAMESPACE
kubectl rollout status deployment/order-service-production -n $NAMESPACE --timeout=10m

# 等待 Production 完全就緒後，將流量切回 Production
echo "⏳ 等待 Production 就緒..."
sleep 60

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

echo ""
echo "✅ 部署完成！"
echo "   版本: $VERSION"
echo "   流量已切換到 Production"

