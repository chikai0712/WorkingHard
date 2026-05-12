# 🔧 故障排除指南

## 問題: .env 檔案權限錯誤

如果遇到 `.env` 檔案權限問題,不用擔心!我們已經在 `docker-compose.yml` 中直接設定了所有必要的環境變數。

## 解決方案

### 步驟 1: 啟動服務

```bash
cd /Users/ckchiu/Desktop/Project/domain-monitoring-system

# 啟動所有服務
docker-compose up -d
```

**注意**: 即使看到 `.env` 權限錯誤訊息,服務仍會正常啟動,因為環境變數已在 `docker-compose.yml` 中設定。

### 步驟 2: 檢查服務狀態

```bash
# 查看所有容器
docker ps | grep dms

# 應該看到 5 個容器:
# - dms-postgres
# - dms-redis
# - dms-api
# - dms-celery-worker
# - dms-celery-beat
```

### 步驟 3: 初始化資料庫

```bash
# 等待 PostgreSQL 啟動 (約 10 秒)
sleep 10

# 執行資料庫遷移
docker-compose exec api alembic upgrade head

# 初始化範例資料
docker-compose exec api python init_data.py
```

### 步驟 4: 驗證功能

```bash
# 測試 API
curl http://localhost:8000

# 應該返回:
# {"status":"healthy","service":"Domain Monitoring System","version":"1.0.0"}

# 訪問 API 文件
open http://localhost:8000/docs
```

## 如果資料庫連接仍然失敗

### 檢查 PostgreSQL 是否就緒

```bash
docker-compose exec postgres pg_isready -U dms_user
```

### 查看 API 日誌

```bash
docker-compose logs api
```

### 手動測試資料庫連接

```bash
docker-compose exec postgres psql -U dms_user -d domain_monitoring -c "SELECT 1;"
```

## 完整重置 (如果需要)

```bash
# 停止並刪除所有容器和資料
docker-compose down -v

# 重新啟動
docker-compose up -d

# 等待服務啟動
sleep 15

# 初始化資料庫
docker-compose exec api alembic upgrade head
docker-compose exec api python init_data.py
```

## 常用命令

```bash
# 查看所有服務日誌
docker-compose logs -f

# 查看特定服務日誌
docker-compose logs -f api
docker-compose logs -f celery-worker

# 重啟特定服務
docker-compose restart api

# 進入容器
docker-compose exec api bash

# 停止服務
docker-compose stop

# 啟動服務
docker-compose start
```

## 手動新增監控網域

```bash
# 使用 curl 新增網域
curl -X POST http://localhost:8000/api/domains \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.com",
    "expected_ips": ["93.184.216.34"],
    "expected_ns": ["a.iana-servers.net", "b.iana-servers.net"],
    "keyword": "Example Domain",
    "check_interval": 300
  }'

# 或使用 API 文件介面
open http://localhost:8000/docs
```

## 配置 Slack 通知 (可選)

如果需要 Slack 通知,修改 `docker-compose.yml` 中的環境變數:

```yaml
api:
  environment:
    - SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

然後重啟服務:

```bash
docker-compose restart api celery-worker celery-beat
```

## 配置 SecurityTrails (可選)

如果需要 SecurityTrails 功能,同樣修改環境變數:

```yaml
api:
  environment:
    - SECURITYTRAILS_API_KEY=your_api_key_here
```

## 需要協助?

如果問題持續存在,請提供以下資訊:

1. Docker 版本: `docker --version`
2. Docker Compose 版本: `docker-compose --version`
3. 容器狀態: `docker-compose ps`
4. API 日誌: `docker-compose logs api | tail -50`

