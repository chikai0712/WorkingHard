# 快速開始指南

## 三步驟啟動系統

### 步驟 1: 設定環境變數

```bash
cd domain-monitoring-system
cp env.example .env
```

編輯 `.env` 檔案,填入以下資訊:

```bash
# 必填 (如需 Slack 通知)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# 選填 (如需 SecurityTrails 功能)
SECURITYTRAILS_API_KEY=your_api_key_here
```

### 步驟 2: 啟動服務

```bash
# 方式 1: 使用快速啟動腳本
./start.sh

# 方式 2: 手動啟動
docker-compose up -d
docker-compose exec api alembic upgrade head
docker-compose exec api python init_data.py
```

### 步驟 3: 驗證功能

```bash
# 執行測試腳本
./test_api.sh

# 或訪問 API 文件
open http://localhost:8000/docs
```

## 常用操作

### 新增監控網域

```bash
curl -X POST http://localhost:8000/api/domains \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "your-domain.com",
    "expected_ips": ["1.2.3.4"],
    "expected_ns": ["ns1.example.com"],
    "keyword": "Welcome",
    "check_interval": 300
  }'
```

### 手動觸發檢查

```bash
curl -X POST http://localhost:8000/api/check/dns \
  -H "Content-Type: application/json" \
  -d '{"domain": "your-domain.com"}'
```

### 查看告警

```bash
# 查看所有告警
curl http://localhost:8000/api/alerts

# 查看未解決的告警
curl http://localhost:8000/api/alerts?is_resolved=false
```

### 查看日誌

```bash
# API 服務日誌
docker-compose logs -f api

# Celery Worker 日誌
docker-compose logs -f celery-worker

# 所有服務日誌
docker-compose logs -f
```

## 服務端點

- **API 服務**: http://localhost:8000
- **API 文件**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 停止服務

```bash
# 停止但保留資料
docker-compose stop

# 停止並刪除容器 (保留資料卷)
docker-compose down

# 完全清除 (包含資料)
docker-compose down -v
```

## 故障排除

### 問題: 容器無法啟動

```bash
# 查看容器狀態
docker-compose ps

# 查看錯誤日誌
docker-compose logs
```

### 問題: 資料庫連接失敗

```bash
# 重啟 PostgreSQL
docker-compose restart postgres

# 檢查資料庫是否就緒
docker-compose exec postgres pg_isready
```

### 問題: Celery 任務未執行

```bash
# 重啟 Celery Worker
docker-compose restart celery-worker celery-beat

# 查看 Redis 連接
docker-compose exec redis redis-cli ping
```

## 下一步

1. 設定 UptimeRobot 監控並配置 Webhook
2. 申請 SecurityTrails API Key
3. 新增更多 ISP DNS 伺服器
4. 自訂告警規則
5. 整合到現有監控系統

詳細文件請參考 `README.md` 和 `DEVELOPMENT.md`。

