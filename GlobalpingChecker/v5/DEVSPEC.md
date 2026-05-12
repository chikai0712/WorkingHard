# GlobalpingChecker V5 — 開發規格文件

> 本文件記錄 V5 開發過程中所有需注意的規格、慣例與限制。
> 每次開新 session 或新功能前必須先讀此文件。

---

## 1. 專案基本資訊

| 項目 | 值 |
|------|----|
| 版本 | V5.0.0 |
| 路徑 | `GlobalpingChecker/v5/` |
| Web Port | 8001（本機 / EC2 相同） |
| DB Port | 5433（PostgreSQL，避免與 v4.1 衝突） |
| DB 名稱 | `globalping_v5_db` |
| Docker network | `globalping_v5_network` |
| 容器名稱 | `globalping_v5_web` / `globalping_v5_postgres` |

---

## 2. 目錄結構與職責

```
v5/
├── app/
│   ├── config.py          # 所有設定值，新增功能必須先在這裡加設定
│   ├── models.py          # 資料庫 ORM 模型，Schema 變更必須同步更新
│   ├── database.py        # DB 連線與初始化，不要動
│   ├── main.py            # FastAPI 路由入口，新增 API 在這裡
│   ├── checker.py         # 核心檢測邏輯，最容易出問題的地方
│   ├── zone_manager.py    # 域名分區邏輯，不要動（從 v4.1 繼承）
│   ├── cycle_scheduler.py # 排程器，不要動（從 v4.1 繼承）
│   ├── node_pool.py       # 節點池管理（V5 已移除重複 ORM 類別）
│   └── node_validator.py  # IP 地理驗證，不要動
├── templates/
│   └── dashboard.html     # 唯一的前端頁面
├── static/                # 靜態資源（目前為空）
├── deploy/
│   └── deploy-v5.sh       # EC2 部署腳本，每次部署前確認 EC2_HOST
├── data/                  # 掛載給 Docker，DB 備份
├── .env                   # 實際環境變數（不進 git）
├── .env.example           # 環境變數範本（進 git）
├── docker-compose.yml     # 本機 + EC2 共用同一份
├── Dockerfile
└── requirements.txt
```

---

## 3. 環境變數規格

### 必填

| 變數 | 說明 |
|------|------|
| `GLOBALPING_TOKEN` | Globalping API token |
| `POSTGRES_PASSWORD` | PostgreSQL 密碼 |
| `DATABASE_URL` | 完整 DB 連線字串 |

### 國家開關（預設只開印尼）

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `ENABLE_INDONESIA` | `true` | 印尼 (ID) |
| `ENABLE_VIETNAM` | `false` | 越南 (VN) |
| `ENABLE_THAILAND` | `false` | 泰國 (TH) |
| `ENABLE_MALAYSIA` | `false` | 馬來西亞 (MY) |
| `ENABLE_PHILIPPINES` | `false` | 菲律賓 (PH) |
| `ENABLE_SINGAPORE` | `false` | 新加坡 (SG) |

### V5 新增設定

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `NODE_POOL_TTL_HOURS` | `24` | 節點池快取有效時間（小時）|
| `NODE_POOL_REFRESH_HOUR` | `3` | 每天幾點自動刷新節點池 |
| `NODES_PER_COUNTRY` | `5` | 每個國家使用幾個節點 |
| `API_QUOTA_WARNING_THRESHOLD` | `50` | 剩餘額度低於此值告警 |
| `API_QUOTA_WAIT_ON_ERROR` | `3600` | API Error 後等待秒數 |
| `TELEGRAM_BOT_TOKEN` | 空 | Telegram Bot（暫未啟用）|
| `TELEGRAM_CHAT_ID` | 空 | Telegram Chat ID |

---

## 4. 資料庫模型注意事項

### V5 相比 V4.1 新增的欄位

| 表 | 欄位 | 說明 |
|----|------|------|
| `domain_results` | `check_duration_ms` | 單域名完整檢測耗時（ms）|
| `test_batches` | `api_calls_used` | 本批次消耗的 API 額度 |
| `node_pool` | `is_top_isp` | 是否為 TOP30 ISP 節點 |
| `alerts` | 整個新表 | Telegram 告警歷史 |
| `domains` | `primary_country` | 主要檢測國家（預設 `ID`）|

### 重要規則

- **`NodePool` ORM 類別只在 `models.py` 定義**，`node_pool.py` 只 import 使用
- **Schema 變更必須同步更新 `models.py`**，`init_db()` 會自動 `create_all`
- 目前不使用 Alembic migration，直接 `create_all`
- 若需要改欄位類型，必須先 `docker compose down -v` 清空資料庫再重啟

---

## 5. API 端點清單

### 繼承自 V4.1

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/` | Dashboard HTML |
| GET | `/api/stats` | 統計數據 |
| GET | `/api/live` | 即時狀態 |
| GET | `/api/progress` | 檢測進度（輪詢用）|
| GET | `/api/cycle` | 當前循環資訊 |
| GET | `/api/schedule` | 排程設定 |
| POST | `/api/check/trigger` | 手動觸發檢測 |
| GET | `/api/zones/{zone}` | 指定區域域名清單 |
| GET | `/api/domains/{domain}` | 域名歷史記錄 |
| GET | `/api/batches` | 批次清單 |
| GET | `/api/logs` | 系統日誌 |
| GET | `/api/nodes/pool` | 節點池清單 |
| POST | `/api/nodes/pool/refresh` | 手動刷新節點池 |
| POST | `/api/domains/reload` | 重新載入域名 |

### V5 新增

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/quota` | 查詢 Globalping API 剩餘額度 |
| GET | `/api/alerts` | Telegram 告警歷史 |
| GET | `/api/recent-results` | 最近一批次檢測結果（Dashboard 常態顯示用）|
| POST | `/api/check/stop` | 暫停當前檢測（完成當前域名後停止）|
| POST | `/api/check/recheck-abnormal` | 重新只檢測異常區域名 |

---

## 6. Docker 操作規範

### 啟動（本機 + EC2 相同指令）

```bash
cd ~/Desktop/Project/GlobalpingChecker/v5
docker compose up --build
```

### 常用指令

```bash
# 停止
docker compose down

# 查看日誌
docker compose logs -f web
docker compose logs -f postgres

# 重置資料庫（謹慎！會刪除所有資料）
docker compose down -v
docker compose up --build

# 進入容器
docker exec -it globalping_v5_web bash
docker exec -it globalping_v5_postgres psql -U globalping -d globalping_v5_db
```

### 注意事項

- **不要在 Cursor IDE 內建 terminal 執行 `docker` 指令**，有 socket 權限問題，請用系統 Terminal.app / iTerm2
- `docker-compose.yml` 本機和 EC2 共用同一份，不要分兩個檔案
- `.env` 不進 git，每個環境（本機 / EC2）各自維護
- Port 8001 / 5433 已避開 v4.1 的 8000 / 5432，兩個版本可同時運行
- `blocked_ips.txt` 有掛載進容器（`:ro`），更新後需重啟 web 容器才生效

---

## 7. 部署流程（EC2）

### 部署前確認

1. `deploy/deploy-v5.sh` 內的 `EC2_HOST` 是正確 IP
2. `~/.ssh/globalping-checker-key.pem` 存在且有正確權限 (`chmod 400`)
3. EC2 上已有 `~/v5/.env`（首次部署需手動建立）

### 執行部署

```bash
bash ~/Desktop/Project/GlobalpingChecker/v5/deploy/deploy-v5.sh
```

### 部署腳本流程

1. 驗證 SSH 金鑰
2. 測試 SSH 連線
3. 打包 `v5/` 目錄（排除 `__pycache__`、`.env`、`data/`）
4. `scp` 上傳 tar.gz 到 EC2 `/tmp/`
5. EC2 上：停舊容器 → 備份 `.env` + `domains.txt` → 解壓 → 恢復設定 → `docker compose up`
6. 等待 10 秒後驗證 `http://$EC2_HOST:8001/api/stats`

### EC2 目錄結構

```
~/v5/        ← 當前版本
~/v5.bak/    ← 上一個版本備份
```

---

## 8. 新增功能的標準流程

1. **先更新 `config.py`** — 新功能的設定值加到 `Settings` class 和 `.env.example`
2. **再更新 `models.py`** — 若需要新欄位或新表
3. **再更新 `main.py`** — 新增 API 端點，同時更新本文件 Section 5
4. **最後更新 `checker.py`** — 若涉及檢測邏輯
5. **更新 `.env.example`** — 加入新的環境變數說明
6. **更新本文件 (DEVSPEC.md)** — 在對應章節記錄變更
7. **更新 STATE.md** — 記錄完成的工作

---

## 9. 已知限制與禁止事項

### 禁止

| 禁止事項 | 原因 |
|----------|------|
| 在 `node_pool.py` 重新定義 `NodePool` ORM 類別 | 已在 `models.py` 定義，重複定義會造成衝突 |
| 在 Cursor IDE 內建 terminal 執行 `docker` 指令 | socket 權限問題 |
| 修改 `zone_manager.py` 的核心分區邏輯 | 影響域名分區行為，破壞現有資料 |
| 修改 `cycle_scheduler.py` 的時間觸發邏輯 | 影響排程，可能造成重複或遺漏檢測 |
| 直接操作 production PostgreSQL | 只透過 API 或 `docker exec psql` |
| 把 `.env` 提交進 git | 包含 token 和密碼 |

### 已知問題（待修復）

| 問題 | 影響 | 優先級 |
|------|------|--------|
| Telegram `notifier.py` 尚未實作 | `alerts` 表只寫入但不發送 | 低 |
| `static/` 目錄為空 | 若前端需要 CSS/JS 本地資源會 404 | 低 |
| 節點池初始化需呼叫 `ip-api.com` | 網路受限時初始化很慢 | 中 |

### 已修復問題

| 問題 | 修復方式 | 修復日期 |
|------|----------|----------|
| Dashboard 時間顯示偏差 8 小時 | `formatDate()` 補 `Z` 後綴，確保瀏覽器正確解析 UTC | 2026-03-19 |
| 自動排程不在台北時間 AM 00:01 觸發 | `CronTrigger` 加入 `timezone=ZoneInfo("Asia/Taipei")` | 2026-03-18 |
| 節點 ISP 多樣性不足（同電信 5 節點）| 節點選取改為 Pass1 ISP多樣性 + Pass2 ASN + Pass3 城市 | 2026-03-14 |
| API 額度耗盡後停止輪詢 | 改為等待整點額度重置後繼續 | 2026-03-18 |
| Dashboard 顯示兩個「立即檢測」按鈕 | 移除重複按鈕 | 2026-03-14 |

---

## 10. 版本歷史

| 版本 | 日期 | 主要變更 |
|------|------|----------|
| V4.1 | 2026-03 | 節點池系統、即時寫入模式、多國家支援 |
| V5.0 | 2026-03-12 | 新增 MY/PH/SG、Telegram 告警架構、`/api/quota`、`/api/alerts`、`check_duration_ms`、`api_calls_used`、`is_top_isp` |
| V5.1 | 2026-03-14 | Dashboard 節點詳情 TOP badge、節點 ISP 多樣性修復、移除重複按鈕 |
| V5.2 | 2026-03-18 | 排程時區修復（Asia/Taipei）、額度驅動輪詢、額度耗盡等整點恢復、`/api/recent-results`、`/api/check/stop`、`/api/check/recheck-abnormal`、Dashboard 歷史結果常態顯示 |
| V5.3 | 2026-03-19 | 時間顯示修復（`formatDate` 補 UTC `Z` 後綴） |

---

## 11. 常用指令速查

```bash
# 本機啟動
cd ~/Desktop/Project/GlobalpingChecker/v5 && docker compose up --build

# 查看 web 日誌
docker compose logs -f web

# 手動觸發檢測
curl -X POST http://localhost:8001/api/check/trigger

# 查詢 API 額度
curl http://localhost:8001/api/quota

# 查詢告警歷史
curl http://localhost:8001/api/alerts

# 查看節點池
curl http://localhost:8001/api/nodes/pool | python3 -m json.tool

# 刷新節點池
curl -X POST http://localhost:8001/api/nodes/pool/refresh

# 重置域名（異常 → 待分類）
curl -X POST http://localhost:8001/api/domains/reset-to-pending
```
