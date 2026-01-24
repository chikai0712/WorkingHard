# 部署策略與自動化

## 📋 部署策略概述

本系統採用 **金絲雀部署（Canary Deployment）** 策略，實現零停機更新與流量漸進式驗證。

### 部署流程

```
1. 代碼提交 → CI/CD Pipeline 觸發
2. 構建 Docker 鏡像 → 推送到 Registry
3. 部署新版本 Pod（金絲雀）→ 10% 流量
4. 監控指標（5-10 分鐘）→ 驗證穩定性
5. 逐步增加流量（10% → 50% → 100%）
6. 完全切換後 → 保留舊版本 24 小時（快速回滾）
```

## 🎯 部署策略對比

### 1. 藍綠部署（Blue-Green）
- **優點**：快速切換，零停機
- **缺點**：需要雙倍資源，成本高
- **適用**：關鍵業務，需要秒級切換

### 2. 金絲雀部署（Canary）
- **優點**：風險低，逐步驗證，資源節省
- **缺點**：切換時間較長（10-30 分鐘）
- **適用**：本系統採用（平衡風險與成本）

### 3. 滾動更新（Rolling Update）
- **優點**：資源節省，平滑過渡
- **缺點**：新舊版本共存，可能不兼容
- **適用**：非關鍵服務

## 🚀 CI/CD Pipeline 設計

### GitLab CI/CD 配置

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy-canary
  - deploy-production

variables:
  DOCKER_REGISTRY: registry.example.com
  IMAGE_NAME: betting-service/order-service
  K8S_NAMESPACE: betting-service

build:
  stage: build
  script:
    - docker build -t $IMAGE_NAME:$CI_COMMIT_SHA -f deploy/docker/Dockerfile.order-service .
    - docker tag $IMAGE_NAME:$CI_COMMIT_SHA $IMAGE_NAME:latest
    - docker push $IMAGE_NAME:$CI_COMMIT_SHA
    - docker push $IMAGE_NAME:latest
  only:
    - main
    - develop

test:
  stage: test
  script:
    - go test ./... -v -coverprofile=coverage.out
    - go tool cover -html=coverage.out -o coverage.html
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.out

deploy-canary:
  stage: deploy-canary
  script:
    - kubectl set image deployment/order-service-canary order-service=$IMAGE_NAME:$CI_COMMIT_SHA -n $K8S_NAMESPACE
    - kubectl rollout status deployment/order-service-canary -n $K8S_NAMESPACE --timeout=5m
    - ./scripts/verify_canary.sh
  environment:
    name: canary
    url: https://canary.betting-service.example.com
  only:
    - main

deploy-production:
  stage: deploy-production
  script:
    - ./scripts/gradual_rollout.sh $CI_COMMIT_SHA
  when: manual  # 需要手動觸發
  environment:
    name: production
    url: https://betting-service.example.com
  only:
    - main
```

## 🔄 金絲雀部署實現

### 1. Kubernetes 配置

#### Canary Deployment

```yaml
# deploy/kubernetes/order-service-canary.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service-canary
  namespace: betting-service
spec:
  replicas: 1  # 10% 流量（總共 10 個 Pod，1 個 Canary）
  selector:
    matchLabels:
      app: order-service
      version: canary
  template:
    metadata:
      labels:
        app: order-service
        version: canary
    spec:
      containers:
      - name: order-service
        image: betting-service/order-service:latest
        ports:
        - containerPort: 8080
        env:
        - name: VERSION
          value: "canary"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
```

#### Production Deployment

```yaml
# deploy/kubernetes/order-service-production.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service-production
  namespace: betting-service
spec:
  replicas: 9  # 90% 流量
  selector:
    matchLabels:
      app: order-service
      version: production
  template:
    metadata:
      labels:
        app: order-service
        version: production
    spec:
      containers:
      - name: order-service
        image: betting-service/order-service:stable
        ports:
        - containerPort: 8080
        env:
        - name: VERSION
          value: "production"
```

#### Service with Traffic Splitting

```yaml
# deploy/kubernetes/order-service-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: order-service
  namespace: betting-service
spec:
  selector:
    app: order-service
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
```

### 2. Istio VirtualService（流量切割）

```yaml
# deploy/kubernetes/istio-virtualservice.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: order-service
  namespace: betting-service
spec:
  hosts:
  - order-service
  http:
  - match:
    - headers:
        x-canary:
          exact: "true"
    route:
    - destination:
        host: order-service
        subset: canary
      weight: 100
  - route:
    - destination:
        host: order-service
        subset: canary
      weight: 10  # 10% 流量到 Canary
    - destination:
        host: order-service
        subset: production
      weight: 90  # 90% 流量到 Production
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: order-service
  namespace: betting-service
spec:
  host: order-service
  subsets:
  - name: canary
    labels:
      version: canary
  - name: production
    labels:
      version: production
```

### 3. 使用 Nginx Ingress（替代方案，無需 Istio）

```yaml
# deploy/kubernetes/nginx-ingress-canary.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: order-service-canary
  namespace: betting-service
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"  # 10% 流量
spec:
  ingressClassName: nginx
  rules:
  - host: betting-service.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: order-service-canary
            port:
              number: 8080
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: order-service-production
  namespace: betting-service
spec:
  ingressClassName: nginx
  rules:
  - host: betting-service.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: order-service-production
            port:
              number: 8080
```

## 📊 自動化部署腳本

### 1. 金絲雀驗證腳本

```bash
#!/bin/bash
# scripts/verify_canary.sh

set -e

NAMESPACE="betting-service"
CANARY_DEPLOYMENT="order-service-canary"
TIMEOUT=600  # 10 分鐘

echo "🔍 開始驗證金絲雀部署..."

# 1. 檢查 Pod 是否就緒
echo "1. 檢查 Pod 狀態..."
kubectl wait --for=condition=ready pod -l version=canary -n $NAMESPACE --timeout=${TIMEOUT}s

# 2. 檢查健康檢查端點
echo "2. 檢查健康檢查端點..."
CANARY_POD=$(kubectl get pod -l version=canary -n $NAMESPACE -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n $NAMESPACE $CANARY_POD -- curl -f http://localhost:8080/health || exit 1

# 3. 檢查錯誤率（從 Prometheus）
echo "3. 檢查錯誤率..."
ERROR_RATE=$(curl -s "http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~'5..'}[5m])" | jq -r '.data.result[0].value[1]')
if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
  echo "❌ 錯誤率過高: $ERROR_RATE"
  exit 1
fi

# 4. 檢查延遲（P99）
echo "4. 檢查延遲..."
P99_LATENCY=$(curl -s "http://prometheus:9090/api/v1/query?query=histogram_quantile(0.99,rate(http_request_duration_seconds_bucket[5m]))" | jq -r '.data.result[0].value[1]')
if (( $(echo "$P99_LATENCY > 0.1" | bc -l) )); then
  echo "❌ P99 延遲過高: ${P99_LATENCY}s"
  exit 1
fi

# 5. 檢查業務指標（注單處理成功率）
echo "5. 檢查業務指標..."
SUCCESS_RATE=$(curl -s "http://prometheus:9090/api/v1/query?query=rate(order_processed_total{status='success'}[5m])/rate(order_processed_total[5m])" | jq -r '.data.result[0].value[1]')
if (( $(echo "$SUCCESS_RATE < 0.99" | bc -l) )); then
  echo "❌ 注單處理成功率過低: $SUCCESS_RATE"
  exit 1
fi

echo "✅ 金絲雀驗證通過！"
```

### 2. 漸進式流量切換腳本

```bash
#!/bin/bash
# scripts/gradual_rollout.sh

set -e

VERSION=$1
NAMESPACE="betting-service"

if [ -z "$VERSION" ]; then
  echo "❌ 請提供版本號"
  exit 1
fi

echo "🚀 開始漸進式部署版本: $VERSION"

# 階段 1: 10% 流量（已通過金絲雀驗證）
echo "📊 階段 1: 10% 流量..."
kubectl patch virtualservice order-service -n $NAMESPACE --type=json -p='
[
  {"op": "replace", "path": "/spec/http/1/route/0/weight", "value": 10},
  {"op": "replace", "path": "/spec/http/1/route/1/weight", "value": 90}
]'
sleep 300  # 等待 5 分鐘

# 驗證指標
./scripts/verify_metrics.sh || {
  echo "❌ 驗證失敗，回滾..."
  ./scripts/rollback.sh
  exit 1
}

# 階段 2: 50% 流量
echo "📊 階段 2: 50% 流量..."
kubectl patch virtualservice order-service -n $NAMESPACE --type=json -p='
[
  {"op": "replace", "path": "/spec/http/1/route/0/weight", "value": 50},
  {"op": "replace", "path": "/spec/http/1/route/1/weight", "value": 50}
]'
sleep 300

./scripts/verify_metrics.sh || {
  echo "❌ 驗證失敗，回滾..."
  ./scripts/rollback.sh
  exit 1
}

# 階段 3: 100% 流量
echo "📊 階段 3: 100% 流量..."
kubectl patch virtualservice order-service -n $NAMESPACE --type=json -p='
[
  {"op": "replace", "path": "/spec/http/1/route/0/weight", "value": 100},
  {"op": "replace", "path": "/spec/http/1/route/1/weight", "value": 0}
]'

# 更新 Production Deployment
kubectl set image deployment/order-service-production order-service=betting-service/order-service:$VERSION -n $NAMESPACE
kubectl rollout status deployment/order-service-production -n $NAMESPACE --timeout=10m

echo "✅ 部署完成！"
```

### 3. 指標驗證腳本

```bash
#!/bin/bash
# scripts/verify_metrics.sh

PROMETHEUS_URL="http://prometheus:9090"
THRESHOLD_ERROR_RATE=0.01
THRESHOLD_P99_LATENCY=0.1
THRESHOLD_SUCCESS_RATE=0.99

# 檢查錯誤率
ERROR_RATE=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=rate(http_requests_total{status=~'5..'}[5m])" | jq -r '.data.result[0].value[1]')
if (( $(echo "$ERROR_RATE > $THRESHOLD_ERROR_RATE" | bc -l) )); then
  echo "❌ 錯誤率過高: $ERROR_RATE > $THRESHOLD_ERROR_RATE"
  exit 1
fi

# 檢查延遲
P99_LATENCY=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=histogram_quantile(0.99,rate(http_request_duration_seconds_bucket[5m]))" | jq -r '.data.result[0].value[1]')
if (( $(echo "$P99_LATENCY > $THRESHOLD_P99_LATENCY" | bc -l) )); then
  echo "❌ P99 延遲過高: ${P99_LATENCY}s > ${THRESHOLD_P99_LATENCY}s"
  exit 1
fi

# 檢查業務成功率
SUCCESS_RATE=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=rate(order_processed_total{status='success'}[5m])/rate(order_processed_total[5m])" | jq -r '.data.result[0].value[1]')
if (( $(echo "$SUCCESS_RATE < $THRESHOLD_SUCCESS_RATE" | bc -l) )); then
  echo "❌ 業務成功率過低: $SUCCESS_RATE < $THRESHOLD_SUCCESS_RATE"
  exit 1
fi

echo "✅ 所有指標正常"
```

### 4. 回滾腳本

```bash
#!/bin/bash
# scripts/rollback.sh

NAMESPACE="betting-service"

echo "🔄 開始回滾..."

# 1. 將流量切回 Production
kubectl patch virtualservice order-service -n $NAMESPACE --type=json -p='
[
  {"op": "replace", "path": "/spec/http/1/route/0/weight", "value": 0},
  {"op": "replace", "path": "/spec/http/1/route/1/weight", "value": 100}
]'

# 2. 縮容 Canary Deployment
kubectl scale deployment order-service-canary --replicas=0 -n $NAMESPACE

# 3. 回滾 Production Deployment（如果已更新）
kubectl rollout undo deployment/order-service-production -n $NAMESPACE

echo "✅ 回滾完成"
```

## 📈 監控與告警

### Prometheus 告警規則

```yaml
# deploy/kubernetes/prometheus-alerts.yaml
groups:
- name: canary_deployment
  interval: 30s
  rules:
  - alert: CanaryHighErrorRate
    expr: rate(http_requests_total{version="canary",status=~"5.."}[5m]) > 0.01
    for: 2m
    annotations:
      summary: "金絲雀版本錯誤率過高"
      description: "Canary 版本錯誤率: {{ $value }}"

  - alert: CanaryHighLatency
    expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{version="canary"}[5m])) > 0.1
    for: 2m
    annotations:
      summary: "金絲雀版本延遲過高"
      description: "Canary P99 延遲: {{ $value }}s"

  - alert: CanaryLowSuccessRate
    expr: rate(order_processed_total{version="canary",status="success"}[5m]) / rate(order_processed_total{version="canary"}[5m]) < 0.99
    for: 2m
    annotations:
      summary: "金絲雀版本業務成功率過低"
      description: "Canary 成功率: {{ $value }}"
```

## 🔐 安全考慮

1. **認證與授權**：CI/CD Pipeline 使用 Service Account 與 RBAC
2. **鏡像簽名**：使用 Docker Content Trust 驗證鏡像完整性
3. **密鑰管理**：使用 Kubernetes Secrets 或外部密鑰管理系統（如 Vault）
4. **審計日誌**：記錄所有部署操作，便於追蹤

## 📝 最佳實踐

1. **版本標籤**：使用 Git Commit SHA 作為鏡像標籤，確保可追溯
2. **保留舊版本**：部署新版本後，保留舊版本 24 小時，便於快速回滾
3. **監控時間**：每個流量階段監控至少 5 分鐘，確保穩定性
4. **自動回滾**：當指標異常時，自動觸發回滾，減少人工干預
5. **通知機制**：部署開始、完成、回滾時發送通知（Slack、Email）

## 🚨 故障處理

### 自動回滾觸發條件

- 錯誤率 > 1% 持續 2 分鐘
- P99 延遲 > 100ms 持續 2 分鐘
- 業務成功率 < 99% 持續 2 分鐘
- Pod 重啟次數 > 3 次/5 分鐘

### 手動回滾

```bash
# 快速回滾到上一個版本
kubectl rollout undo deployment/order-service-production -n betting-service

# 回滾到指定版本
kubectl rollout undo deployment/order-service-production --to-revision=2 -n betting-service
```

---

**最後更新**：2025-01-XX

