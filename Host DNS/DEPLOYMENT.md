# 部署指南

本文檔提供 Host DNS Resolver 的詳細部署步驟與注意事項。

## 目錄

- [前置需求](#前置需求)
- [環境準備](#環境準備)
- [部署流程](#部署流程)
- [驗證與測試](#驗證與測試)
- [監控與告警](#監控與告警)
- [故障排除](#故障排除)

## 前置需求

### 基礎設施

- **Kubernetes 集群**：版本 1.20 或更高
- **AWS EKS**（或支援 AWS NLB 的環境）
- **網路**：VPC 配置完成，子網劃分正確
- **安全組**：允許 53/UDP、53/TCP 從互聯網訪問

### 工具需求

- `kubectl` 已安裝並配置
- `kustomize`（可選，可用 `kubectl apply -k` 替代）
- `dig` 或 `dnsperf`（用於測試）

### 資源需求

每個 Pod 建議配置：
- **CPU**：4 cores（requests: 500m, limits: 4000m）
- **記憶體**：4GB（requests: 1Gi, limits: 4Gi）
- **節點**：至少 3 個節點，分佈在不同可用區

## 環境準備

### 1. 節點層級配置

在部署前，建議先配置節點層級的 sysctl 參數以優化 UDP 性能：

```bash
# 手動執行（需要 root 權限）
sudo ./scripts/setup-node-sysctl.sh

# 或使用 DaemonSet（推薦）
kubectl apply -f k8s/daemonset-sysctl.yaml
```

關鍵參數：
- `net.netfilter.nf_conntrack_max`: 根據預期 QPS 計算
- `net.netfilter.nf_conntrack_udp_timeout`: 10 秒
- `net.core.rmem_max`: 128MB
- `net.core.wmem_max`: 128MB

### 2. 檢查集群狀態

```bash
# 確認集群連接
kubectl cluster-info

# 檢查節點資源
kubectl top nodes

# 確認有足夠的節點
kubectl get nodes
```

### 3. 準備配置文件

所有配置文件已包含在 `k8s/` 目錄中，但部署前請檢查：

- **ConfigMap 配置**：確認 dnsdist 和 Unbound 的配置符合需求
- **資源限制**：根據實際環境調整 CPU/記憶體限制
- **副本數**：根據流量需求調整 `replicas`（建議至少 3）

## 部署流程

### 方法 1：使用部署腳本（推薦）

```bash
# 確保腳本有執行權限
chmod +x scripts/deploy.sh

# 執行部署
./scripts/deploy.sh
```

腳本會自動：
1. 檢查前置需求
2. 應用所有 Kubernetes 資源
3. 等待部署就緒
4. 顯示服務資訊

### 方法 2：手動部署

```bash
# 1. 創建 namespace
kubectl apply -f k8s/namespace.yaml

# 2. 創建 ConfigMaps
kubectl apply -f k8s/configmap-dnsdist.yaml
kubectl apply -f k8s/configmap-unbound.yaml
kubectl apply -f k8s/configmap-vector-dnstap.yaml

# 3. 部署應用
kubectl apply -f k8s/deployment-dns-resolver.yaml

# 4. 創建 Service
kubectl apply -f k8s/service-dns-resolver.yaml

# 5. 配置監控（可選）
kubectl apply -f k8s/servicemonitor-prometheus.yaml
kubectl apply -f k8s/prometheus-rules.yaml
```

### 方法 3：使用 Kustomize

```bash
# 使用 kustomize 構建並應用
kubectl apply -k k8s/

# 或使用 kustomize 命令
kustomize build k8s/ | kubectl apply -f -
```

## 驗證與測試

### 1. 檢查部署狀態

```bash
# 檢查 Pod 狀態
kubectl get pods -n dns -l app=dns-resolver

# 檢查 Service
kubectl get svc -n dns dns-resolver

# 查看 Pod 日誌
kubectl logs -n dns -l app=dns-resolver -c dnsdist
kubectl logs -n dns -l app=dns-resolver -c unbound
```

### 2. 獲取 LoadBalancer IP

```bash
# 獲取外部 IP（可能需要幾分鐘）
kubectl get svc dns-resolver -n dns -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# 或查看完整資訊
kubectl describe svc dns-resolver -n dns
```

### 3. 基本功能測試

```bash
# 使用測試腳本
./scripts/test-dns.sh -s <LOADBALANCER_IP>

# 或手動測試
dig @<LOADBALANCER_IP> google.com
dig @<LOADBALANCER_IP> google.com +tcp
```

### 4. 性能測試

```bash
# 使用 dnsperf（需先安裝）
dnsperf -s <LOADBALANCER_IP> -d queryfile.txt -Q 1000 -l 30

# 或使用測試腳本
./scripts/test-dns.sh -s <LOADBALANCER_IP> -q 1000 -t 30
```

### 5. 驗證 Proxy Protocol

```bash
# 檢查 dnsdist 是否正確接收真實 IP
kubectl logs -n dns -l app=dns-resolver -c dnsdist | grep "client"

# 檢查動態限流是否工作
kubectl exec -n dns <POD_NAME> -c dnsdist -- dnsdist -c "showDynBlocks()"
```

## 監控與告警

### Prometheus 指標

部署後，以下指標將自動暴露：

**dnsdist 指標**：
- `dnsdist_queries`: 查詢總數
- `dnsdist_responses`: 回應總數
- `dnsdist_dynblock_numblo`: 被封鎖的 IP 數
- `dnsdist_pool_servers_up/down`: 後端健康狀態

**Unbound 指標**：
- `unbound_time_up`: 運行時間
- `unbound_struct_msg_cache_hits/misses`: 快取命中率
- `unbound_ratelimit_exceeded`: 限流觸發次數

### 告警規則

已配置的告警規則（見 `k8s/prometheus-rules.yaml`）：

- **DNSResolverDown**: Pod 下線
- **DNSResolverHighErrorRate**: 錯誤率過高
- **DNSResolverHighLatency**: 延遲過高
- **DNSResolverWaterTortureAttack**: 檢測到 Water Torture 攻擊
- **DNSResolverBackendDown**: Unbound 後端下線
- **DNSResolverLowCacheHitRate**: 快取命中率過低

### 查看告警

```bash
# 如果使用 Prometheus Operator
kubectl get prometheusrules -n dns

# 查看告警狀態
# 訪問 Prometheus UI 或使用 Alertmanager
```

## 故障排除

### 常見問題

#### 1. Pod 無法啟動

```bash
# 檢查 Pod 狀態
kubectl describe pod <POD_NAME> -n dns

# 查看事件
kubectl get events -n dns --sort-by='.lastTimestamp'

# 檢查配置
kubectl get configmap dnsdist-config -n dns -o yaml
kubectl get configmap unbound-config -n dns -o yaml
```

#### 2. LoadBalancer IP 無法獲取

```bash
# 檢查 Service
kubectl describe svc dns-resolver -n dns

# 檢查 AWS NLB（如果在 AWS）
aws elbv2 describe-load-balancers --region <REGION>
```

#### 3. DNS 解析失敗

```bash
# 檢查 dnsdist 日誌
kubectl logs -n dns -l app=dns-resolver -c dnsdist --tail=100

# 檢查 Unbound 日誌
kubectl logs -n dns -l app=dns-resolver -c unbound --tail=100

# 測試後端連接
kubectl exec -n dns <POD_NAME> -c dnsdist -- dig @127.0.0.1:5353 google.com
```

#### 4. 高延遲或丟包

```bash
# 檢查節點資源
kubectl top nodes
kubectl top pods -n dns

# 檢查 conntrack 使用率
kubectl exec -n dns <POD_NAME> -c dnsdist -- cat /proc/sys/net/netfilter/nf_conntrack_count

# 檢查 UDP buffer
kubectl exec -n dns <POD_NAME> -c unbound -- ss -un
```

#### 5. Proxy Protocol 不工作

```bash
# 確認 Service annotation
kubectl get svc dns-resolver -n dns -o yaml | grep proxy-protocol

# 檢查 dnsdist 配置
kubectl exec -n dns <POD_NAME> -c dnsdist -- cat /etc/dnsdist/dnsdist.conf | grep ProxyProtocol
```

### 調試命令

```bash
# 進入 Pod
kubectl exec -it -n dns <POD_NAME> -c dnsdist -- /bin/bash

# 查看 dnsdist 控制台
kubectl exec -n dns <POD_NAME> -c dnsdist -- dnsdist -c

# 查看 Unbound 統計
kubectl exec -n dns <POD_NAME> -c unbound -- unbound-control stats

# 查看動態封鎖
kubectl exec -n dns <POD_NAME> -c dnsdist -- dnsdist -c "showDynBlocks()"
```

## 升級與維護

### 配置更新

```bash
# 更新 ConfigMap
kubectl apply -f k8s/configmap-dnsdist.yaml
kubectl apply -f k8s/configmap-unbound.yaml

# 重啟 Pod 以應用新配置
kubectl rollout restart deployment/dns-resolver -n dns
```

### 擴展

```bash
# 增加副本數
kubectl scale deployment dns-resolver -n dns --replicas=5

# 或編輯 Deployment
kubectl edit deployment dns-resolver -n dns
```

### 回滾

```bash
# 查看歷史版本
kubectl rollout history deployment/dns-resolver -n dns

# 回滾到上一版本
kubectl rollout undo deployment/dns-resolver -n dns

# 回滾到特定版本
kubectl rollout undo deployment/dns-resolver -n dns --to-revision=2
```

## 安全建議

1. **更改預設密碼**：更新 dnsdist webserver 的密碼和 API key
2. **RBAC 配置**：限制 ConfigMap 的寫入權限
3. **網路策略**：使用 NetworkPolicy 限制 Pod 間通信
4. **IP 遮罩**：確保 DNSTAP 日誌中的 IP 已正確遮罩
5. **定期更新**：保持容器鏡像和 Kubernetes 版本更新

## 參考文檔

- [架構規劃審查與優化報告 v1.01](./docs/優化報告-v1.01.md)
- [dnsdist 官方文檔](https://dnsdist.org/)
- [Unbound 官方文檔](https://www.nlnetlabs.nl/documentation/unbound/)

