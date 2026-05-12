# GlobalpingChecker V5

智能循環 DNS 監控系統 — 多國家版本。

---

## V5 vs V4.1 差異

| 功能 | V4.1 | V5 |
|------|------|----|
| 支援國家 | ID / VN / TH | ID / VN / TH / MY / PH / SG |
| API 額度查詢端點 | ✗ | `GET /api/quota` |
| Telegram 告警 | ✗ | ✅（zone change / API error）|
| 告警歷史記錄 | ✗ | `GET /api/alerts` |
| check_duration_ms | ✗ | ✅（每域名耗時）|
| api_calls_used | ✗ | ✅（每批次 API 消耗）|
| nodes_per_country 設定 | 硬編碼 3 | `.env` 可調整 |
| API Error 等待時間 | 硬編碼 3600s | `API_QUOTA_WAIT_ON_ERROR` |
| 節點池刷新時間 | 硬編碼凌晨 3:00 | `NODE_POOL_REFRESH_HOUR` |
| Port（避免與 v4.1 衝突） | 8000 / 5432 | 8001 / 5433 |
| Docker network | globalping_v41_network | globalping_v5_network |
| 排程時區 | UTC（偏差 8 小時）| Asia/Taipei（正確）|
| 額度耗盡行為 | 停止輪詢 | 等待整點額度重置後繼續 |
| ISP 節點多樣性 | ASN 去重（同電信多節點）| ISP/ASN/城市三層去重 |
| Dashboard 時間顯示 | UTC 顯示（偏差 8 小時）| 自動轉本地時間 |
| Dashboard 歷史結果 | 僅檢測中顯示 | 常態顯示最近一批次結果 |
| 暫停/重檢控制 | ✗ | `POST /api/check/stop`、`/api/check/recheck-abnormal` |

---

## 目錄結構

```
v5/
├── app/
│   ├── __init__.py
│   ├── config.py          # 設定（含新增的 V5 欄位）
│   ├── models.py          # 資料庫模型（含 Alert、NodePool.is_top_isp）
│   ├── database.py        # DB 初始化
│   ├── main.py            # FastAPI 應用與路由
│   ├── checker.py         # 域名檢測邏輯
│   ├── zone_manager.py    # 從 v4.1 複製，無須修改
│   ├── cycle_scheduler.py # 從 v4.1 複製，無須修改
│   ├── node_pool.py       # 從 v4.1 複製，建議更新 is_top_isp
│   └── node_validator.py  # 從 v4.1 複製，無須修改
├── templates/             # 從 v4.1 複製（或重新設計）
├── static/                # 從 v4.1 複製
├── deploy/                # 部署腳本
├── domains.txt            # 從 v4.1 複製
├── blocked_ips.txt        # 從 v4.1 複製
├── .env.example           # 環境變數範本
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## 快速啟動

### 1. 從 v4.1 複製必要檔案

```bash
cd /path/to/GlobalpingChecker

# 複製共用邏輯模組
cp v4.1/app/zone_manager.py   v5/app/
cp v4.1/app/cycle_scheduler.py v5/app/
cp v4.1/app/node_pool.py      v5/app/
cp v4.1/app/node_validator.py v5/app/

# 複製靜態資源
cp -r v4.1/templates/ v5/
cp -r v4.1/static/    v5/

# 複製資料檔案
cp v4.1/domains.txt     v5/
cp v4.1/blocked_ips.txt v5/
```

### 2. 建立 .env

```bash
cd v5/
cp .env.example .env
# 編輯 .env，填入 GLOBALPING_TOKEN 和 POSTGRES_PASSWORD
```

### 3. 啟動服務

```bash
docker-compose up -d --build
```

### 4. 驗證

```bash
curl http://localhost:8001/api/stats
curl http://localhost:8001/api/quota
```

---

## 新增 API 端點

### `GET /api/quota`
查詢目前 Globalping API 剩餘額度。

```json
{
  "remaining": 250,
  "warning": false,
  "threshold": 50
}
```

### `GET /api/alerts`
查詢 Telegram 告警歷史（需設定 `TELEGRAM_BOT_TOKEN`）。

```
GET /api/alerts?limit=20&alert_type=ZONE_CHANGE
```

---

## 從 V4.1 遷移

V5 使用**獨立的資料庫**（`globalping_v5_db`）和**獨立的 Docker 容器**，與 V4.1 完全隔離，可同時運行。

- V4.1 Dashboard: http://your-server:8000
- V5 Dashboard:   http://your-server:8001

如需遷移舊資料，請使用 `alembic` 或手動匯出 / 匯入 PostgreSQL。
