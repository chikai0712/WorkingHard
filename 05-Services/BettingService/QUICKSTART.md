# 快速開始指南

## 前置需求

- Go 1.21+
- Docker & Docker Compose
- PostgreSQL 15+ (或使用 Docker)
- Redis 7+ (或使用 Docker)
- Kafka (或使用 Docker)

## 步驟 1: 啟動基礎設施

```bash
# 啟動 PostgreSQL, Redis, Kafka
docker-compose -f deploy/docker/docker-compose.yml up -d

# 等待服務啟動（約 30 秒）
sleep 30

# 初始化數據庫
psql -h localhost -U postgres -f scripts/init_db.sql
```

## 步驟 2: 安裝依賴

```bash
cd BettingService
go mod download
```

## 步驟 3: 配置

配置文件位於 `configs/config.yaml`，可根據環境調整：

```yaml
server:
  port: 8080

database:
  host: localhost
  port: 5432
  user: postgres
  password: postgres
  dbname: betting_db

redis:
  host: localhost
  port: 6379

kafka:
  brokers:
    - localhost:9092
```

## 步驟 4: 啟動服務

### 方式 1: 使用 Makefile

```bash
# 構建
make build

# 運行 Order Service
make run-order

# 運行 Gateway (新終端)
make run-gateway
```

### 方式 2: 直接運行

```bash
# 終端 1: 啟動 Order Service
cd cmd/order-service
go run main.go

# 終端 2: 啟動 Gateway
cd cmd/gateway
go run main.go
```

## 步驟 5: 測試 API

### 創建注單

```bash
curl -X POST http://localhost:8080/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 12345,
    "game_type": "slot",
    "bet_amount": 100.00,
    "order_no": "ORDER_001"
  }'
```

### 查詢注單

```bash
curl http://localhost:8080/api/v1/orders/ORDER_001
```

### 查詢注單列表

```bash
curl "http://localhost:8080/api/v1/orders?user_id=12345&page=1&page_size=20"
```

### 結算注單

```bash
curl -X PUT http://localhost:8080/api/v1/orders/ORDER_001/settle \
  -H "Content-Type: application/json" \
  -d '{
    "win_amount": 150.00
  }'
```

## 步驟 6: 監控

### Prometheus

訪問: http://localhost:9090

### Grafana

訪問: http://localhost:3000
- 用戶名: admin
- 密碼: admin

## 壓力測試

```bash
# 使用 wrk (推薦)
wrk -t12 -c1000 -d30s \
  -s scripts/test_order.json \
  http://localhost:8080/api/v1/orders

# 或使用 Apache Bench
ab -n 100000 -c 1000 \
  -p scripts/test_order.json \
  -T application/json \
  http://localhost:8080/api/v1/orders
```

## 常見問題

### 1. 數據庫連接失敗

檢查 PostgreSQL 是否啟動：
```bash
docker ps | grep postgres
```

### 2. Redis 連接失敗

檢查 Redis 是否啟動：
```bash
docker ps | grep redis
```

### 3. Kafka 連接失敗

檢查 Kafka 是否啟動：
```bash
docker ps | grep kafka
```

### 4. 端口被佔用

修改 `configs/config.yaml` 中的端口配置。

## 下一步

- 閱讀 [架構設計文檔](docs/Architecture.md)
- 閱讀 [API 文檔](docs/API.md)
- 查看 [部署指南](docs/Deployment.md)

