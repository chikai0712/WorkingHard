# GlobalpingChecker V4.1 - 快速開始指南

## 🎯 兩種方案對比

| 方案 | 用途 | 時間 | 難度 |
|------|------|------|------|
| **模擬數據模式** | 演示、測試 UI | 5 分鐘 | ⭐ 簡單 |
| **AWS 部署** | 生產環境 | 30 分鐘 | ⭐⭐⭐ 中等 |

---

## 方案 1️⃣：模擬數據模式（立即體驗）

### 步驟 1：生成模擬數據

```bash
cd /Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1
source venv/bin/activate
python generate_mock_data.py
```

**預期輸出：**
```
🚀 開始生成模擬數據...
📋 創建檢測循環...
  ✅ 循環 #3 已建立
📝 創建測試批次...
  ✅ 批次 #3 已建立
🔍 更新域名狀態和檢測結果...
  已處理 100/100 個域名...
  ✅ 已處理 100 個域名

📊 模擬數據統計:
  清潔: 45
  被封鎖: 35
  超時: 10
  警告: 5
  部分: 3
  API 錯誤: 2

✅ 模擬數據生成完成！
```

### 步驟 2：訪問監控頁面

打開瀏覽器訪問：
```
http://127.0.0.1:8000
```

**你會看到：**
- ✅ 正常區域名：45 個
- ❌ 異常區域名：35 個
- ⏳ 待分類域名：20 個
- 📊 完整的檢測統計
- 📈 批次歷史記錄

---

## 方案 2️⃣：AWS 部署（生產環境）

### 快速部署（5 步）

#### 步驟 1：啟動 EC2 實例
- 實例類型：t3.medium
- 操作系統：Ubuntu 20.04 LTS
- 存儲：30GB
- 安全組：開放 8000 端口

#### 步驟 2：SSH 連接
```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

#### 步驟 3：一鍵部署腳本

```bash
# 複製以下命令到 EC2 實例

cd /opt
sudo git clone https://github.com/your-repo/GlobalpingChecker.git
cd GlobalpingChecker/v4.1
sudo chown -R ubuntu:ubuntu /opt/GlobalpingChecker

# 安裝依賴
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置環境
cp .env.example .env
# 編輯 .env，確保 GLOBALPING_TOKEN 正確

# 初始化數據庫
python generate_mock_data.py

# 啟動應用
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 步驟 4：訪問應用
```
http://your-instance-ip:8000
```

#### 步驟 5：配置 systemd 服務（可選）

參考 `AWS_DEPLOYMENT_GUIDE.md` 中的 systemd 配置部分

---

## 🔍 驗證部署

### 檢查應用狀態

```bash
# 檢查 API 是否響應
curl http://127.0.0.1:8000/api/stats

# 預期輸出
{
  "zone_stats": {
    "NORMAL": 45,
    "ABNORMAL": 35,
    "PENDING": 20
  },
  "total_domains": 100,
  "normal_count": 45,
  "abnormal_count": 35,
  "pending_count": 20,
  "last_check_time": "2026-03-12T10:06:15.517Z",
  "cycle_info": {...}
}
```

### 檢查數據庫

```bash
cd /Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1
source venv/bin/activate
python << 'EOF'
import sqlite3
db = sqlite3.connect('data/globalping_results.db')
c = db.cursor()
c.execute('SELECT COUNT(*) FROM test_batches')
print(f"批次數: {c.fetchone()[0]}")
c.execute('SELECT COUNT(*) FROM domain_results')
print(f"檢測結果: {c.fetchone()[0]}")
db.close()
EOF
```

---

## 📊 監控頁面功能

### 主頁面 (/)
- 📈 統計數據概覽
- 🔄 當前循環信息
- ⏰ 最後檢測時間

### API 端點

| 端點 | 功能 |
|------|------|
| `GET /api/stats` | 獲取統計數據 |
| `GET /api/cycle` | 獲取循環信息 |
| `GET /api/zones/{zone}` | 獲取區域域名 |
| `GET /api/batches` | 獲取批次列表 |
| `GET /api/batches/{id}` | 獲取批次詳情 |
| `GET /api/domains/{domain}` | 獲取域名歷史 |
| `POST /api/check/trigger` | 手動觸發檢測 |

---

## 🚀 下一步

### 模擬模式後
1. 查看監控頁面的完整功能
2. 理解數據結構
3. 準備 AWS 部署

### AWS 部署後
1. 應用會自動開始檢測
2. 每 90 分鐘檢測一次
3. 監控頁面實時更新

---

## 📝 文件清單

| 文件 | 用途 |
|------|------|
| `generate_mock_data.py` | 生成模擬數據 |
| `manual_trigger_check.py` | 手動觸發檢測 |
| `test_api_correct.py` | 測試 API 連接 |
| `AWS_DEPLOYMENT_GUIDE.md` | AWS 部署詳細指南 |
| `API_TEST_GUIDE.md` | API 測試指南 |

---

## ❓ 常見問題

### Q: 模擬數據會覆蓋真實數據嗎？
A: 不會。模擬數據只是添加新的批次和結果，不會刪除現有數據。

### Q: 如何切換回真實檢測？
A: 在 AWS 上部署應用，它會自動開始真實檢測。

### Q: API Token 無效怎麼辦？
A: 訪問 https://app.globalping.io 生成新的 Token，更新 `.env` 文件。

### Q: 如何停止檢測？
A: 停止應用進程或修改排程器配置。

---

## 🎯 推薦流程

1. **現在** → 運行模擬數據，體驗監控頁面
2. **今天** → 在 AWS 上部署應用
3. **明天** → 應用開始真實檢測，監控頁面填充真實數據

---

**準備好了嗎？開始吧！** 🚀
