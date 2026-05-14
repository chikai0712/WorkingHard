# GlobalpingChecker V4.1 - 智能循環檢測系統

## 🔄 循環檢測邏輯

### 第一循環：異常區檢測 (AM 1:00 - AM 9:00)
- **檢測對象**: 異常區 + 待分類區的域名
- **檢測次數**: 最多 10 次
- **邏輯**:
  - 檢測異常域名，記錄錯誤訊息並分析
  - 如果域名變正常，移到正常區
  - 持續檢測直到完成 10 次或切換時間

### 第二循環：正常區檢測 (AM 9:00 - AM 1:00)
- **檢測對象**: 正常區的域名
- **檢測次數**: 持續檢測直到切換
- **邏輯**:
  - 檢測正常域名，確認是否仍然正常
  - 如果域名變異常，移到異常區
  - 持續監控正常域名的穩定性

## 📊 域名區域

| 區域 | 說明 |
|------|------|
| **正常區 (NORMAL)** | 連續檢測正常的域名 |
| **異常區 (ABNORMAL)** | 檢測異常的域名，需要持續監控 |
| **待分類 (PENDING)** | 尚未檢測的新域名 |

## 🚀 快速開始

### 本地測試

```bash
# 1. 創建 .env 文件
cp .env.example .env
# 編輯 .env 填入 GLOBALPING_TOKEN 和 POSTGRES_PASSWORD

# 2. 啟動服務
docker-compose up -d

# 3. 訪問 Dashboard
open http://localhost:8000
```

### AWS 部署

```bash
# 1. 上傳到 EC2
scp -r v4.1/ ec2-user@your-ip:/opt/globalping/

# 2. SSH 登入並啟動
ssh ec2-user@your-ip
cd /opt/globalping
docker-compose up -d
```

## 📡 API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/` | GET | Web Dashboard |
| `/api/stats` | GET | 統計數據 |
| `/api/cycle` | GET | 當前循環信息 |
| `/api/schedule` | GET | 排程配置 |
| `/api/check/trigger` | POST | 手動觸發檢測 |
| `/api/zones/{zone}` | GET | 獲取區域域名 |
| `/api/batches` | GET | 批次列表 |
| `/api/batches/{id}` | GET | 批次詳情 |
| `/api/batches/{id}/results` | GET | 批次結果 |
| `/api/domains/{domain}` | GET | 域名歷史 |
| `/api/logs` | GET | 系統日誌 |

## ⚙️ 配置說明

| 環境變數 | 默認值 | 說明 |
|----------|--------|------|
| `CHECK_INTERVAL_MINUTES` | 90 | 檢測間隔（分鐘） |
| `ABNORMAL_CHECK_HOUR` | 1 | 異常區檢測開始時間 (AM) |
| `NORMAL_CHECK_HOUR` | 9 | 正常區檢測開始時間 (AM) |
| `MAX_ITERATIONS` | 10 | 第一循環最大檢測次數 |

## 📁 目錄結構

```
v4.1/
├── app/
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── database.py        # 資料庫連接
│   ├── models.py          # 資料模型
│   ├── zone_manager.py    # 區域管理器
│   ├── cycle_scheduler.py # 循環排程器
│   ├── checker.py         # 域名檢測器
│   └── main.py            # FastAPI 應用
├── templates/
│   └── dashboard.html     # Web Dashboard
├── static/
├── domains.txt            # 域名列表
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## 📈 版本更新

### V4.1 新功能
- ✅ 智能循環檢測（異常區/正常區）
- ✅ 自動時間切換 (AM 1:00 / AM 9:00)
- ✅ 域名區域管理（正常區/異常區/待分類）
- ✅ 區域變更歷史追蹤
- ✅ 錯誤訊息分析和記錄
- ✅ 循環進度顯示
