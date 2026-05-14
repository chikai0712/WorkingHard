# 全方位網域資產監控系統 (Domain Integrity Monitoring System)

一個中心化的監控平台,透過三層維度(全球可用性、區域 DNS 完整性、資產歷史溯源)的交叉驗證,在 Domain 被劫持、ISP 阻擋或解析異常時,提供最準確的告警資訊。

## 系統架構

### 三層防護體系

1. **UptimeRobot (全球可用性與內容校驗)**
   - 監控全球用戶是否能正常存取服務
   - 關鍵字監控檢查網頁內容
   - Webhook 整合即時告警

2. **區域 DNS 輪詢 (ISP 污染與局部解析監控)**
   - 偵測特定地區、特定 ISP 的 DNS 污染
   - 維護各國主要 ISP 的 DNS Server 清單
   - 白名單比對與交叉驗證

3. **SecurityTrails API (網域資產與隱蔽劫持監控)**
   - NS 紀錄監控(P0 級告警)
   - WHOIS 異動監控
   - IP 歷史與畫像分析

## 技術棧

- **後端框架**: FastAPI (Python 3.11+)
- **資料庫**: PostgreSQL 16
- **任務隊列**: Celery + Redis
- **DNS 查詢**: aiodns (非同步)
- **告警通道**: Slack Webhook
- **容器化**: Docker + Docker Compose

## 快速開始

### 1. 環境準備

```bash
# 複製專案
cd domain-monitoring-system

# 建立環境變數檔案
cp env.example .env

# 編輯 .env 填入必要的 API Keys
# - SECURITYTRAILS_API_KEY
# - SLACK_WEBHOOK_URL
```

### 2. 啟動服務

```bash
# 使用 Docker Compose 啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f api
```

### 3. 初始化資料庫

```bash
# 進入 API 容器
docker-compose exec api bash

# 執行資料庫遷移
alembic upgrade head

# 退出容器
exit
```

### 4. 新增監控網域

```bash
# 使用 API 新增網域
curl -X POST http://localhost:8000/api/domains \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.com",
    "expected_ips": ["1.2.3.4", "5.6.7.8"],
    "expected_ns": ["ns1.example.com", "ns2.example.com"],
    "keyword": "Welcome",
    "check_interval": 300
  }'
```

### 5. 新增 ISP DNS 伺服器

```bash
# 新增台灣中華電信 DNS
curl -X POST http://localhost:8000/api/nameservers \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "TW",
    "isp_name": "中華電信",
    "dns_server": "168.95.1.1"
  }'

# 新增 Google Public DNS
curl -X POST http://localhost:8000/api/nameservers \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "US",
    "isp_name": "Google",
    "dns_server": "8.8.8.8"
  }'
```

## API 文件

啟動服務後,訪問以下網址查看完整 API 文件:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 核心功能

### 1. 網域管理

- `POST /api/domains` - 建立網域監控
- `GET /api/domains` - 列出所有網域
- `GET /api/domains/{id}` - 取得網域詳情
- `PUT /api/domains/{id}` - 更新網域設定
- `DELETE /api/domains/{id}` - 刪除網域監控

### 2. DNS 伺服器管理

- `POST /api/nameservers` - 新增 DNS 伺服器
- `GET /api/nameservers` - 列出所有 DNS 伺服器
- `GET /api/nameservers?country_code=TW` - 依國家篩選

### 3. 監控與告警

- `POST /api/check/dns` - 手動觸發 DNS 檢查
- `GET /api/alerts` - 查看告警列表
- `GET /api/events` - 查看監控事件

### 4. Webhook

- `POST /webhook/uptimerobot` - 接收 UptimeRobot 告警

## 告警等級

系統會根據決策引擎分析結果,產生不同等級的告警:

| 等級 | 根因 | 說明 | 處理優先級 |
|------|------|------|-----------|
| **P0** | domain_hijacked | 網域所有權遭劫持 (NS 變動) | 🚨 Critical |
| **P1** | isp_blocked | 區域性 ISP 封鎖或 DNS 污染 | ⚠️ High |
| **P1** | content_defacement | 網站內容被竄改 | ⚠️ High |
| **P2** | config_error | DNS 配置錯誤 | ℹ️ Normal |
| **P2** | whois_changed | WHOIS 資訊變動 | ℹ️ Normal |

## 自動化任務

系統使用 Celery Beat 執行定期任務:

- **每 5 分鐘**: 檢查所有啟用的網域
- **每 1 小時**: 健康檢查所有 DNS 伺服器

## 專案結構

```
domain-monitoring-system/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 主應用
│   ├── config.py            # 配置管理
│   ├── database.py          # 資料庫連接
│   ├── models.py            # SQLAlchemy 模型
│   ├── schemas.py           # Pydantic Schemas
│   ├── dns_checker.py       # DNS 查詢模組
│   ├── decision_engine.py   # 決策引擎
│   ├── notifier.py          # Slack 通知
│   ├── securitytrails.py    # SecurityTrails API
│   └── tasks.py             # Celery 任務
├── alembic/
│   └── versions/
│       └── 001_initial_schema.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── env.example
└── README.md
```

## 開發指南

### 本地開發

```bash
# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt

# 啟動 PostgreSQL 和 Redis (使用 Docker)
docker-compose up -d postgres redis

# 執行資料庫遷移
alembic upgrade head

# 啟動 API 服務
uvicorn app.main:app --reload --port 8000

# 啟動 Celery Worker (另一個終端)
celery -A app.tasks.celery_app worker --loglevel=info

# 啟動 Celery Beat (另一個終端)
celery -A app.tasks.celery_app beat --loglevel=info
```

### 執行測試

```bash
# 安裝測試依賴
pip install pytest pytest-asyncio

# 執行測試
pytest tests/
```

## 常見 ISP DNS 列表

### 台灣
- 中華電信: 168.95.1.1, 168.95.192.1
- 台灣固網: 61.31.233.1, 61.31.1.1

### 中國
- 中國電信: 202.96.128.86, 202.96.134.133
- 中國聯通: 123.125.81.6, 140.207.198.6

### 美國
- Google: 8.8.8.8, 8.8.4.4
- Cloudflare: 1.1.1.1, 1.0.0.1

### 日本
- NTT: 210.141.112.163
- OCN: 210.196.3.183

## 監控最佳實踐

1. **設定合理的檢查間隔**: 建議 5-10 分鐘
2. **維護 DNS 白名單**: 定期更新預期的 IP 列表
3. **關鍵字監控**: 選擇網頁中穩定且唯一的字串
4. **告警去重**: 系統自動處理,避免告警風暴
5. **定期檢視**: 每週檢視告警趨勢和誤報率

## 故障排除

### 資料庫連接失敗
```bash
# 檢查 PostgreSQL 是否運行
docker-compose ps postgres

# 查看資料庫日誌
docker-compose logs postgres
```

### Celery 任務未執行
```bash
# 檢查 Redis 連接
docker-compose exec redis redis-cli ping

# 查看 Celery Worker 日誌
docker-compose logs celery-worker
```

### DNS 查詢超時
- 檢查網路連接
- 調整 `DNS_TIMEOUT` 設定
- 移除不健康的 DNS 伺服器

## 授權

MIT License

## 聯絡方式

如有問題或建議,請開 Issue 或 Pull Request。

