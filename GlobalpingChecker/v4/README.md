# GlobalpingChecker V4

## 域名監控系統 - 印尼 ISP DNS 檢測

自動化域名監控系統，每 90 分鐘檢測域名在印尼各 ISP 的連通狀態，並提供 Web Dashboard 查看結果。

## 功能特點

### 1. 自動定時檢測
- 每 90 分鐘自動執行檢測（可配置）
- 支援手動觸發檢測
- 自動重試失敗的域名

### 2. 狀態分類說明

| 狀態 | 說明 |
|------|------|
| ✅ **CLEAN** | 正常連通 - 所有節點都能正常訪問，HTTP 回應 2xx/3xx |
| 🚨 **BLOCKED** | DNS 污染 - 解析到已知的封鎖 IP（如 36.86.63.185） |
| ⏱️ **TIMEOUT** | 完全超時 - 所有節點都無法連接或無回應 |
| ⚠️ **WARNING** | 服務異常 - HTTP 回應非正常狀態碼（4xx/5xx） |
| 🔄 **PARTIAL** | 部分異常 - 部分節點正常，部分節點異常 |
| ❌ **API_ERROR** | 檢測失敗 - API 請求錯誤或超時 |

### 3. 節點詳細資訊
每次檢測記錄包含：
- **ISP**: 網路服務提供商名稱
- **ASN**: 自治系統編號
- **City**: 節點所在城市
- **Node IP**: 檢測節點的 IP 地址
- **Target IP**: 域名解析到的目標 IP
- **HTTP Code**: HTTP 回應狀態碼
- **Response Time**: 回應時間（毫秒）

### 4. PostgreSQL 資料庫
- 完整的測試歷史記錄
- 域名狀態變化追蹤
- 支援複雜查詢和報表

### 5. Web Dashboard
- 即時統計數據
- 狀態分類詳情
- 歷史記錄查詢
- 域名詳細資訊

## 快速開始

### 本地開發

1. **複製配置文件**
```bash
cd v4
cp .env.example .env
```

2. **編輯 .env 文件**
```bash
# 設定你的 Globalping Token
GLOBALPING_TOKEN=your_token_here

# PostgreSQL 連接
DATABASE_URL=postgresql://globalping:password@localhost:5432/globalping_db
```

3. **啟動服務**
```bash
docker-compose up -d
```

4. **訪問 Dashboard**
```
http://localhost:8000
```

### AWS 部署

1. **配置 AWS CLI**
```bash
aws configure
```

2. **執行部署腳本**
```bash
cd v4/aws
./deploy.sh
```

3. **複製應用程式代碼到 EC2**
```bash
scp -i your-key.pem -r ../v4/* ec2-user@<PUBLIC_IP>:/opt/globalping/
```

4. **在 EC2 上執行安裝**
```bash
ssh -i your-key.pem ec2-user@<PUBLIC_IP>
cd /opt/globalping
./aws/setup-app.sh
```

## 目錄結構

```
v4/
├── app/
│   ├── __init__.py
│   ├── config.py        # 配置管理
│   ├── database.py      # 資料庫模型
│   ├── checker.py       # 域名檢測邏輯
│   ├── scheduler.py     # 定時排程
│   └── main.py          # FastAPI 應用
├── templates/
│   └── dashboard.html   # Web Dashboard
├── static/              # 靜態文件
├── aws/
│   ├── cloudformation.yaml  # AWS 基礎設施
│   ├── deploy.sh           # 部署腳本
│   └── setup-app.sh        # 應用安裝腳本
├── domains.txt          # 域名列表
├── requirements.txt     # Python 依賴
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/` | Web Dashboard |
| GET | `/api/stats` | 統計數據 |
| GET | `/api/batches` | 測試批次列表 |
| GET | `/api/batches/{id}` | 批次詳情 |
| GET | `/api/batches/{id}/results` | 批次結果 |
| GET | `/api/batches/{id}/classification` | 分類詳情 |
| GET | `/api/domains/{domain}` | 域名歷史 |
| GET | `/api/history/changes` | 狀態變化記錄 |
| GET | `/api/scheduler/logs` | 排程日誌 |
| POST | `/api/check/trigger` | 手動觸發檢測 |

## 配置說明

### 環境變數

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 連接字串 | - |
| `GLOBALPING_TOKEN` | Globalping API Token | - |
| `CHECK_INTERVAL_MINUTES` | 檢測間隔（分鐘） | 90 |
| `DOMAINS_FILE` | 域名列表文件 | domains.txt |
| `HOST` | Web 服務監聽地址 | 0.0.0.0 |
| `PORT` | Web 服務端口 | 8000 |

### domains.txt 格式

```
# 註釋行
example.com
another-domain.com
```

## 資料庫表結構

### test_batches - 測試批次
- `batch_id`: 批次 ID
- `test_date`: 測試時間
- `total_domains`: 總域名數
- `clean_count`: 正常數量
- `blocked_count`: 封鎖數量
- `timeout_count`: 超時數量
- `warning_count`: 警告數量
- `partial_count`: 部分異常數量
- `api_error_count`: 錯誤數量
- `duration_seconds`: 耗時
- `is_scheduled`: 是否為排程執行

### domain_results - 域名結果
- `result_id`: 結果 ID
- `batch_id`: 批次 ID
- `domain`: 域名
- `overall_status`: 整體狀態
- `test_date`: 測試時間

### node_details - 節點詳情
- `detail_id`: 詳情 ID
- `result_id`: 結果 ID
- `node_isp`: ISP 名稱
- `node_asn`: ASN
- `node_city`: 城市
- `node_ip`: 節點 IP
- `target_ip`: 目標 IP
- `status`: 狀態
- `http_code`: HTTP 狀態碼
- `response_time_ms`: 回應時間

### domain_history - 狀態變化歷史
- `history_id`: 歷史 ID
- `domain`: 域名
- `previous_status`: 之前狀態
- `current_status`: 當前狀態
- `changed_at`: 變化時間

## 常用命令

```bash
# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f web

# 重啟服務
docker-compose restart

# 手動觸發檢測
curl -X POST http://localhost:8000/api/check/trigger

# 查看統計
curl http://localhost:8000/api/stats

# 進入 PostgreSQL
docker-compose exec postgres psql -U globalping -d globalping_db
```

## 版本歷史

- **V4.0.0** (2026-03-06)
  - 全新 Python 架構
  - PostgreSQL 資料庫
  - FastAPI Web 框架
  - 自動定時排程
  - Web Dashboard
  - AWS 一鍵部署

## 授權

MIT License
