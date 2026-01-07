# Host DNS（對外 Resolver）架構規劃與實作

本專案針對「dnsdist + Unbound 於 Kubernetes」的遞迴解析平台，提供涵蓋網路拓撲、系統配置、可觀測與營運的完整實作方案，以達成高併發、限流、防禦與快速復原目標。

## 📋 專案結構

```
Host DNS/
├── README.md                          # 本文件
├── docs/
│   ├── 優化報告-v1.01.md             # 架構規劃審查與優化報告 v1.01
│   ├── 流程圖.md                      # 詳細流程圖（10個關鍵流程）
│   └── 地端部署設備清單.md            # 地端部署設備規格與數量清單
├── config/
│   ├── dnsdist.conf                   # dnsdist 完整配置（含所有優化）
│   └── unbound.conf                   # Unbound 完整配置（含 RFC 8767）
├── k8s/
│   ├── namespace.yaml                 # DNS namespace
│   ├── configmap-dnsdist.yaml        # dnsdist ConfigMap
│   ├── configmap-unbound.yaml        # Unbound ConfigMap
│   ├── configmap-vector-dnstap.yaml  # Vector DNSTAP 配置
│   ├── deployment-dns-resolver.yaml  # 主部署清單（dnsdist + Unbound + Sidecar）
│   ├── service-dns-resolver.yaml     # AWS NLB Service（含 Proxy Protocol）
│   ├── servicemonitor-prometheus.yaml # Prometheus 監控配置
│   ├── prometheus-rules.yaml          # Prometheus 告警規則
│   ├── daemonset-sysctl.yaml         # 節點 sysctl 配置（可選）
│   └── kustomization.yaml            # Kustomize 配置
└── scripts/
    ├── deploy.sh                      # 一鍵部署腳本
    ├── test-dns.sh                    # DNS 測試腳本
    └── setup-node-sysctl.sh          # 節點層級 sysctl 配置腳本
```

## 🚀 快速開始

### 前置需求

- Kubernetes 集群（1.20+）
- kubectl 已配置並可連接集群
- AWS EKS（或支援 AWS NLB 的環境）
- 足夠的節點資源（建議每個 Pod 4 CPU + 4GB RAM）

### 部署步驟

1. **配置節點 sysctl（可選但建議）**
   ```bash
   # 在每個節點上執行
   sudo ./scripts/setup-node-sysctl.sh
   # 或使用 DaemonSet
   kubectl apply -f k8s/daemonset-sysctl.yaml
   ```

2. **部署 DNS Resolver**
   ```bash
   # 使用部署腳本（推薦）
   ./scripts/deploy.sh
   
   # 或手動部署
   kubectl apply -k k8s/
   ```

3. **驗證部署**
   ```bash
   # 檢查 Pod 狀態
   kubectl get pods -n dns
   
   # 獲取 LoadBalancer IP
   kubectl get svc dns-resolver -n dns
   
   # 測試 DNS 解析
   ./scripts/test-dns.sh -s <LOADBALANCER_IP>
   ```

### 配置說明

詳細的配置說明與優化建議請參考：
- **[架構規劃審查與優化報告 v1.01](./docs/優化報告-v1.01.md)** - 完整的技術審查與優化建議
- **[詳細流程圖](./docs/流程圖.md)** - 10個關鍵流程圖（架構、請求處理、限流、復原等）
- **[地端部署設備清單](./docs/地端部署設備清單.md)** - 地端部署設備規格、數量與成本估算
- **[地端部署指南](./docs/地端部署指南.md)** - 地端部署詳細步驟與配置
- **[部署指南](./DEPLOYMENT.md)** - 詳細的部署步驟與故障排除
- **[原始規劃文件 v1.0](#)** - 基礎架構規劃（本文檔下方）

## 🔑 關鍵優化點（v1.01）

根據優化報告，本實作包含以下關鍵改進：

1. **來源 IP 保留**：使用 AWS NLB + Proxy Protocol v2 + IP Target Mode
2. **RFC 8767 正確實作**：正確配置 serve-expired 參數，避免幽靈域名風險
3. **高併發優化**：SO_REUSEPORT、UDP buffer 調優、conntrack 優化
4. **動態限流**：Ring Buffer + DynBlockRulesGroup 防護
5. **可觀測性**：DNSTAP + Vector Sidecar + Prometheus 監控
6. **快速復原**：Lazy Health Checks + 過期快取兜底

詳細說明請參閱 [優化報告](./docs/優化報告-v1.01.md)。

---

# Host DNS（對外 Resolver）可行性方案 v1.0

本方案針對「dnsdist + Unbound 於 Kubernetes」的遞迴解析平台，提供涵蓋網路拓撲、系統配置、可觀測與營運的落地建議，以達成高併發、限流、防禦與快速復原目標。

---

## 1. 網路拓撲與 AWS NLB 策略

### 1.1 進出路徑與 VPC 規劃
- **Ingress**：AWS Network Load Balancer (NLB) → Kubernetes Service (type: LoadBalancer) → dnsdist DaemonSet/Deployment（hostNetwork=false） → Unbound Sidecar/Deployment。
- **子網**：NLB 置於公開子網，dnsdist/Unbound Pod 於私有子網；Security Group 僅允許 53/UDP、53/TCP 來源為互聯網/NLB Health Check IP。
- **Pod 佈局**：每 AZ 至少 2 個 dnsdist Pod；Unbound 以 Sidecar 或獨立 Deployment (但須與 dnsdist 同 Node pool) 以降低橫向流量。

### 1.2 來源 IP 保留策略
| 策略 | 優點 | 風險 | 建議 |
| --- | --- | --- | --- |
| `ExternalTrafficPolicy: Local` | 原生保留 Client IP、低延遲 | Pod 分布不均產生黑洞 | 可作為 fallback，但需配合 Pod topology spread + 自動化損毀轉移 |
| **Proxy Protocol v2（建議）** | 跨節點負載均衡、維持真實 IP | 需 LB/dnsdist/Unbound 端端支援 | **採用 AWS NLB + Proxy Protocol v2 + TargetType=ip** |

**K8s Service Annotation**
```yaml
service.beta.kubernetes.io/aws-load-balancer-proxy-protocol: "*"
service.beta.kubernetes.io/aws-load-balancer-type: "nlb-ip"
service.beta.kubernetes.io/aws-load-balancer-nlb-target-type: "ip"
service.beta.kubernetes.io/aws-load-balancer-healthcheck-port: "53"
```

### 1.3 conntrack 與節點 sysctl
- `net.netfilter.nf_conntrack_max = QPS_peak * conn_duration * safety_factor`（例如 400k QPS、15 秒、1.5 倍 → 9M entries）。
- `net.netfilter.nf_conntrack_udp_timeout = 10s`、`nf_conntrack_udp_timeout_stream = 30s` 以快速回收。
- 若採 `target-type: ip`，大部分 UDP 不進 conntrack，但仍對 Kube-proxy 服務流量與管理面需調優。

---

## 2. dnsdist 邊緣層設計

### 2.1 SO_REUSEPORT 與執行緒調度
- 依 Pod requests/limits 分配 CPU：例如 4 vCPU → `addLocal(..., {reusePort=true})` 重複 4 次。
- 建議將 dnsdist Deployment `podAntiAffinity=topology.kubernetes.io/zone`，確保多 AZ 承載。

### 2.2 動態限流與攻擊防護
```lua
setRingBuffersSize(1_000_000)
local dbr = dynBlockRulesGroup()
dbr:setQueryRate(100, 10, "Exceeded query rate", 60)
dbr:setRCodeRate(DNSRCode.SERVFAIL, 50, 10, "SERVFAIL storm", 60)
dbr:setRCodeRate(DNSRCode.NXDOMAIN, 200, 10, "NXDOMAIN flood", 60)
function maintenance() dbr:apply() end
```
- **Water Torture**：監控 SERVFAIL/NXDOMAIN 速率 + 後端 Unbound latency 指標組合警示。
- **ACL 分層**：Security Group 過濾國家/網段、dnsdist ACL 保留 0.0.0.0/0 但以 DynBlock rules 即時封鎖。

### 2.3 健康檢查與容錯
- `healthCheckMode='lazy'`、`lazyHealthCheckThreshold=0.3` 代表 30% 查詢失敗才啟動主動檢查。
- 兜底邏輯：
```lua
addAction(PoolAvailableRule("recursive"), PoolAction("recursive"))
addAction(CacheHitResponseRule(), CacheResponseAction())
addAction(AllRule(), RCodeAction(DNSRCode.SERVFAIL))
```
- 所有 Unbound 都失效時，至少返回 SERVFAIL 促使客戶端 failover，而非 silent drop。

---

## 3. Unbound 遞迴層最佳化

### 3.1 RFC 8767 Serving Stale
| 參數 | 建議值 | 說明 |
| --- | --- | --- |
| `serve-expired` | yes | 啟用過期快取 |
| `serve-expired-ttl` | 86400 秒 | 過期資料最長 24h |
| `serve-expired-client-timeout` | 1800 ms | 超過 1.8 秒才回退 |
| `serve-expired-reply-ttl` | 30 秒 | 促使 Client 快速刷新 |
- 搭配 `serve-expired-client-only: yes` 確保先嘗試新查詢。

### 3.2 快取/併發與 DNSSEC
- `num-threads = Pod_CPU`，`msg-cache-slabs = rrset-cache-slabs = 2^ceil(log2(num-threads))`。
- `prefetch: yes`、`prefetch-key: yes`；對於熱門域名 TTL < 10% 時自動刷新。
- `so-rcvbuf: 4m`、`so-sndbuf: 4m`，避免 UDP buffer 滿。
- DNSSEC 驗證：若流量高，將 `cache-max-negative-ttl` 限制為 10s，降低 NXDOMAIN cache 被濫用。

### 3.3 Proxy Protocol 與 Sidecar
- Unbound `proxy-protocol-port: 5353`，並啟用 `log-servfail: yes` 供 dnsdist lazy 健檢判斷。
- **DNSTAP Sidecar**：在 Pod 內掛載 `/var/run/dnstap/dnstap.sock`，使用 `vectordnstap` 或 `golang-dnstap` 發送至 Kafka/Vector Agent。
- Pod 資源示例：`requests: cpu 500m, memory 1Gi`；`limits: cpu 2000m, memory 4Gi`，確保 cache 不被 OOMKiller 回收。

---

## 4. 可觀測性與營運

### 4.1 DNSTAP Pipeline
1. dnsdist/Unbound 啟用 dnstap，輸出到 unix socket。
2. Sidecar Vector 收集，進行 **IP Masking ( /24 for IPv4, /48 for IPv6 )**，再以 gRPC 或 HTTP 推送到集中式 ClickHouse。
3. 定義資料保留政策：原始封包 7 天、匯總指標 90 天。

### 4.2 Prometheus 指標與告警
| 元件 | 指標 | 告警條件 |
| --- | --- | --- |
| dnsdist | `dnsdist_dynblock_numblo` | 持續 > 10 表示攻擊，觸發 Security 團隊調查 |
| dnsdist | `dnsdist_pool_servers_down` | 任一 Pool down > 30s → PagerDuty |
| Unbound | `unbound_time_up` | < 1 表示執行緒停擺 |
| Unbound | `unbound_thread_mem_cache_hits/misses` | 呈現 cache hit rate，低於 80% 需擴大 cache |
| Unbound | `unbound_ratelimit_exceeded` | 提醒外部攻擊或設定過嚴 |

### 4.3 測試與演練
- **壓測工具**：dnsperf/resperf + 自建隨機子域 generator。
- **Scenario**：
  1. 400k QPS 正常流量 → 驗證延遲 < 20ms。
  2. Water Torture 攻擊 → 應在 dnsdist DynBlock 60s 內生效。
  3. 上游 (Authoritative) 掛掉 → 觀察 Unbound serve-expired 行為與客戶端 TTL。
- **自動化**：在 Argo/CD pipeline 中加入 `kubectl exec` 執行合成查詢，並將結果 push 至 SLO Dashboard。

---

## 5. 風險控管與未來擴展

### 5.1 Gap & Mitigation
| 缺口 | 風險 | 解法 |
| --- | --- | --- |
| 來源 IP 遺失 | 限流失效、攻擊偵測無效 | 強制 Proxy Protocol v2 + NLB ip target |
| Serve-expired 配置不當 | Ghost domain、錯誤 IP 長期存在 | 設 `serve-expired-ttl/reply-ttl`、演練故障 |
| conntrack 滿載 | UDP 丟包、服務中斷 | NLB-ip 直送 Pod + sysctl 調整 + 監控 `nf_conntrack_count` |
| 日誌同步 IO | 高延遲、CPU 飆升 | dnstap + Sidecar 非同步；禁用 Syslog 全量落地 |
| 健康檢查震盪 | 後端過載 | Lazy HC + 追蹤查詢錯誤率 |

### 5.2 法遵與資安
- dnstap log 資料遮罩、加密傳輸；只保留必要欄位 (query name, type, masked IP)。
- RBAC：拆分運維/分析/開發角色，dnsdist/Unbound ConfigMap 僅 CICD Service Account 可寫。
- 資料保留：符合 GDPR/地方法規，訂定刪除流程。

### 5.3 長期路線圖
- **eBPF / AF_XDP**：dnsdist 支援與 `xdp://` listener；可在 QPS > 1M 時將 Packet dispatch 下沉至 kernel bypass。
- **Anycast + 多區部署**：透過 BGP Anycast 公告多區 VIP，並以 CoreDNS/dnsdist 做地理導向。
- **自動化政策**：結合 L7 攻擊偵測 (Anomaly Detection) 與動態限流門檻調整；納入 Infrastructure as Code (Terraform + ArgoCD)。

---

## 6. 附件
- `docs/diagrams/network-topology.drawio`（建議加入，更易與網路團隊溝通）
- `manifests/dnsdist-service.yaml`、`manifests/unbound-statefulset.yaml`
- `scripts/loadtest/dnsperf-water-torture.sh`

> 此專案需與 SRE、安全、法遵協作，建議於 Q1 完成 PoC（單區 100k QPS），Q2 扩充多區並接入正式告警流程。

