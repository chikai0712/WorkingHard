# 高併發注單服務架構 (High-Concurrency Betting Service)

## 📋 專案概述

這是一個基於 Golang 的高併發注單服務架構，採用微服務設計，支援大規模並發處理、高可用性與水平擴展。

## 🏗️ 架構設計

### 系統架構圖

```
                    ┌─────────────┐
                    │   Client    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ API Gateway  │ (Golang - 負載均衡、限流、認證)
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼─────┐      ┌────▼─────┐      ┌────▼─────┐
   │ Order    │      │ Order    │      │ Order    │
   │ Service  │      │ Service  │      │ Service  │ (Golang - 高併發處理)
   │ (Pod 1)  │      │ (Pod 2)  │      │ (Pod N)  │
   └────┬─────┘      └────┬─────┘      └────┬─────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼─────┐      ┌────▼─────┐      ┌────▼─────┐
   │  Kafka   │      │  Redis   │      │PostgreSQL│
   │ (消息隊列)│      │  (緩存)  │      │ (數據庫) │
   └──────────┘      └──────────┘      └──────────┘
```

### 核心組件

1. **API Gateway**：統一入口、負載均衡、限流、認證
2. **Order Service**：注單處理服務（高併發、Goroutine Pool）
3. **Storage Service**：數據存儲服務（Redis + PostgreSQL）
4. **Kafka**：異步消息處理、事件驅動
5. **Prometheus + Grafana**：監控與可觀測性

## 🚀 技術棧

- **語言**：Golang 1.21+
- **框架**：Gin (HTTP), gRPC
- **數據庫**：PostgreSQL 15+
- **緩存**：Redis 7+
- **消息隊列**：Apache Kafka
- **容器化**：Docker, Kubernetes
- **監控**：Prometheus, Grafana
- **日誌**：ELK Stack (可選)

## 💡 技術選型理由

### Golang 1.21+
**選擇理由：**
- **高併發原生支持**：Goroutine 輕量級協程，單機可輕鬆支援數十萬並發，完美契合注單服務的高併發需求
- **優秀的性能**：編譯型語言，執行效率接近 C/C++，P99 延遲可控制在 50ms 以內
- **內存管理**：GC 優化成熟，適合長時間運行的服務，減少內存洩漏風險
- **豐富的生態**：標準庫完善，第三方庫豐富（Gin、Kafka、Redis 等），開發效率高
- **部署簡單**：單一可執行文件，無需運行時環境，容器化部署體積小

**對比其他語言：**
- vs Java：啟動更快，內存佔用更小，無 JVM 開銷
- vs Python：性能提升 10-100 倍，適合高 QPS 場景
- vs Node.js：更好的 CPU 密集型任務處理能力

### Gin (HTTP 框架)
**選擇理由：**
- **高性能**：基於 `httprouter`，路由匹配速度快，QPS 可達 100,000+
- **中間件生態**：豐富的中間件（認證、限流、日誌、監控），開發效率高
- **易用性**：API 設計簡潔，學習曲線平緩，團隊上手快
- **活躍社區**：GitHub 70k+ stars，文檔完善，問題解決速度快

**對比其他框架：**
- vs Echo：性能相近，但 Gin 生態更成熟
- vs Fiber：Gin 更穩定，生產環境驗證更多

### gRPC
**選擇理由：**
- **高性能通信**：基於 HTTP/2，支援多路復用，延遲低於 REST API 30-50%
- **類型安全**：Protocol Buffers 強類型定義，減少接口錯誤
- **流式處理**：支援雙向流，適合實時數據推送場景
- **跨語言支持**：服務間通信標準化，便於微服務架構擴展

**適用場景：**
- 服務間內部通信（Order Service ↔ Storage Service）
- 需要低延遲的關鍵路徑

### PostgreSQL 15+
**選擇理由：**
- **ACID 保證**：強一致性，確保注單數據準確性，防止重複扣款或結算錯誤
- **豐富的數據類型**：JSONB、數組、時間戳等，靈活存儲注單相關數據
- **強大的查詢能力**：複雜查詢性能優秀，支援多維度統計分析
- **可靠性**：成熟穩定，金融級別數據庫，適合關鍵業務場景
- **開源免費**：無授權費用，TCO 低

**對比其他數據庫：**
- vs MySQL：PostgreSQL 在複雜查詢和並發寫入性能更優
- vs MongoDB：ACID 保證更強，適合金融場景
- vs TiDB：PostgreSQL 更成熟，運維成本更低

### Redis 7+
**選擇理由：**
- **極低延遲**：內存存儲，讀寫延遲 < 1ms，適合熱點數據緩存
- **高吞吐量**：單機可達 100,000+ OPS，滿足高併發讀取需求
- **豐富的數據結構**：String、Hash、Set、Sorted Set，靈活實現各種緩存策略
- **原子操作**：SETNX、INCR 等原子操作，完美實現分散式鎖，防止重複提交
- **持久化選項**：RDB + AOF，可選持久化，平衡性能與可靠性

**使用場景：**
- 注單熱點數據緩存（減少數據庫壓力 80%+）
- 分散式鎖（防止重複創建注單）
- 限流計數器（Token Bucket 實現）

### Apache Kafka
**選擇理由：**
- **高吞吐量**：單機可達百萬級消息/秒，滿足大規模異步處理需求
- **持久化存儲**：消息持久化到磁盤，不丟失，適合關鍵業務事件
- **分散式架構**：水平擴展，支援多分區、多副本，高可用性
- **順序保證**：分區內消息有序，確保注單處理順序
- **解耦設計**：生產者與消費者解耦，便於後續擴展（統計、審計、風控等）

**使用場景：**
- 注單創建事件異步處理（不阻塞主流程）
- 後續擴展：統計分析、審計日誌、風控檢測

**對比其他消息隊列：**
- vs RabbitMQ：Kafka 吞吐量更高，適合大規模場景
- vs RocketMQ：Kafka 生態更成熟，運維工具更豐富

### Docker
**選擇理由：**
- **環境一致性**：開發、測試、生產環境一致，減少「在我機器上能跑」問題
- **快速部署**：秒級啟動，比傳統虛擬機快 10-100 倍
- **資源隔離**：進程級隔離，資源利用率高
- **標準化**：業界標準，CI/CD 集成簡單

### Kubernetes
**選擇理由：**
- **自動擴展**：HPA 根據 CPU/內存自動擴縮容，應對流量波動
- **服務發現**：自動服務發現與負載均衡，無需手動配置
- **故障自愈**：Pod 異常自動重啟，服務自動遷移，可用性 99.95%+
- **資源管理**：精細化資源限制，避免單一服務影響整體系統
- **滾動更新**：零停機部署，業務不中斷

**對比其他編排工具：**
- vs Docker Swarm：Kubernetes 功能更強大，生態更完善
- vs Nomad：Kubernetes 標準化程度更高，人才更容易招聘

### Prometheus + Grafana
**選擇理由：**
- **Prometheus**：
  - 拉取模式，不影響業務服務性能
  - 時間序列數據庫，查詢性能優秀
  - 豐富的指標類型（Counter、Gauge、Histogram），適合監控各種業務指標
  - Alertmanager 整合，支援告警規則
- **Grafana**：
  - 豐富的可視化圖表，直觀展示系統狀態
  - 支援多數據源（Prometheus、InfluxDB 等）
  - 告警通知整合（Email、Slack、PagerDuty）

**監控指標：**
- QPS、延遲、錯誤率（業務指標）
- CPU、內存、連接數（系統指標）
- 數據庫連接池、Redis 操作延遲（中間件指標）

### ELK Stack (可選)
**選擇理由：**
- **集中化日誌**：統一收集、存儲、查詢所有服務日誌
- **全文搜索**：Elasticsearch 強大的搜索能力，快速定位問題
- **可視化分析**：Kibana Dashboard，分析日誌趨勢
- **日誌保留**：長期存儲，滿足審計需求

**適用場景：**
- 生產環境日誌分析與問題排查
- 審計日誌長期存儲
- 日誌驅動的業務分析

## 📁 專案結構

```
BettingService/
├── cmd/                    # 應用入口
│   ├── gateway/           # API Gateway 服務
│   ├── order-service/     # 注單處理服務
│   └── storage-service/   # 數據存儲服務
├── internal/              # 內部包
│   ├── gateway/           # Gateway 業務邏輯
│   ├── order/             # 注單處理邏輯
│   ├── storage/           # 數據存儲邏輯
│   └── common/            # 共用工具
├── pkg/                   # 可重用包
│   ├── config/            # 配置管理
│   ├── logger/            # 日誌工具
│   └── metrics/           # 監控指標
├── deploy/                # 部署配置
│   ├── docker/           # Docker 配置
│   └── kubernetes/       # K8s 配置
├── docs/                  # 文檔
├── scripts/               # 腳本
└── go.mod                 # Go 模組
```

## 🎯 核心特性

### 高併發處理
- **Goroutine Pool**：控制並發數量，避免資源耗盡
- **Channel Buffering**：異步處理，提升吞吐量
- **連接池**：數據庫和 Redis 連接池優化
- **批量處理**：批量寫入數據庫，減少 I/O

### 高可用性
- **服務發現**：Kubernetes Service Discovery
- **健康檢查**：Liveness/Readiness Probes
- **自動擴展**：HPA (Horizontal Pod Autoscaler)
- **故障轉移**：多副本部署

### 性能優化
- **Redis 緩存**：熱點數據緩存，降低數據庫壓力
- **異步處理**：Kafka 異步處理非關鍵路徑
- **數據分片**：按用戶 ID 或時間分片
- **索引優化**：數據庫索引優化

## 📊 性能指標

- **QPS**：支援 100,000+ QPS
- **延遲**：P99 延遲 < 50ms
- **可用性**：99.95%+
- **並發連接**：支援 10,000+ 並發連接

## 🛠️ 快速開始

### 前置需求

- Go 1.21+
- Docker & Docker Compose
- Kubernetes (可選)

### 本地開發

```bash
# 1. 啟動基礎設施（Kafka, Redis, PostgreSQL）
docker-compose -f deploy/docker/docker-compose.yml up -d

# 2. 啟動 API Gateway
cd cmd/gateway
go run main.go

# 3. 啟動 Order Service
cd cmd/order-service
go run main.go

# 4. 啟動 Storage Service
cd cmd/storage-service
go run main.go
```

### 測試

```bash
# 運行單元測試
go test ./...

# 運行壓力測試
cd scripts
./load_test.sh
```

## 📈 監控與日誌

- **Metrics**：Prometheus 收集指標
- **Dashboard**：Grafana 可視化
- **Logs**：結構化日誌輸出
- **Tracing**：分散式追蹤（可選）

## 🔒 安全特性

- **認證**：JWT Token 認證
- **限流**：Rate Limiting (Token Bucket)
- **加密**：HTTPS/TLS
- **輸入驗證**：參數驗證與清理

## 📝 API 文檔

詳見 `docs/API.md`

## 🚢 部署

### 部署策略

本系統採用 **金絲雀部署（Canary Deployment）** 策略，實現零停機更新與流量漸進式驗證：

1. **金絲雀部署**：新版本先部署 1 個 Pod，接收 10% 流量
2. **自動驗證**：監控錯誤率、延遲、業務成功率 5-10 分鐘
3. **漸進式切換**：驗證通過後，逐步增加流量（10% → 50% → 100%）
4. **自動回滾**：指標異常時自動回滾，減少人工干預

詳見 [部署策略文檔](docs/Deployment.md)

### Docker 部署

```bash
docker-compose -f deploy/docker/docker-compose.yml up -d
```

### Kubernetes 部署

```bash
# 1. 創建命名空間
kubectl apply -f deploy/kubernetes/namespace.yaml

# 2. 部署 Production 版本
kubectl apply -f deploy/kubernetes/order-service.yaml

# 3. 部署 Canary 版本（用於流量切割）
kubectl apply -f deploy/kubernetes/order-service-canary.yaml

# 4. 配置流量切割（Istio 或 Nginx Ingress）
kubectl apply -f deploy/kubernetes/istio-virtualservice.yaml
```

### CI/CD 自動化部署

```bash
# GitLab CI/CD 自動觸發
git push origin main

# 流程：
# 1. 自動構建 Docker 鏡像
# 2. 自動部署到 Canary 環境（10% 流量）
# 3. 自動驗證指標
# 4. 手動觸發生產環境部署（漸進式切換）
```

## 📚 文檔

### 核心文檔
- [完整架構文檔](docs/Architecture-Complete.md) - **推薦閱讀**
- [架構圖文檔](docs/Architecture-Diagrams.md) - 詳細架構圖
- [API 文檔](docs/API.md)

### 部署與運維
- [部署策略](docs/Deployment.md) - 金絲雀部署、漸進式切換
- [生產環境訪問控制](docs/Production-Access-Control.md) - 零信任架構

### 安全與合規
- [安全掃描與訪問控制](docs/Security-Scanning-and-Access-Control.md) - 代碼掃描、鏡像掃描
- [GitLab 版本控制與稽核](docs/GitLab-版本控制與稽核.md) - 版本控制策略、稽核機制

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request

## 📄 授權

MIT License

---

**最後更新**：2025-01-XX

