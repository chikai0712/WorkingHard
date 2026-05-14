# 股票資訊儀表板系統

## 📋 專案概述

這是一個自動化股票資訊抓取與顯示系統，可以自動從多個資料來源抓取股票相關資訊，並在網頁儀表板上即時顯示。

## 🎯 功能特點

### 核心功能
- ✅ **自動化資料抓取**：定時從股票 API 抓取最新資料
- ✅ **即時儀表板**：美觀的網頁介面顯示股票資訊
- ✅ **多股票監控**：同時監控多支股票
- ✅ **歷史資料**：儲存歷史價格和成交量資料
- ✅ **技術指標**：計算並顯示常用技術指標（規劃中）
- ✅ **價格趨勢圖表**：視覺化價格走勢（規劃中）
- ✅ **即時更新**：自動刷新最新資料

### 顯示資訊
- 📊 即時股價（開盤、最高、最低、收盤）
- 📈 成交量與成交額
- 💹 漲跌幅度與百分比
- 📉 K 線圖（規劃中）
- 📊 技術指標（規劃中）
- 📰 相關新聞與公告（規劃中）

## 🏗️ 系統架構

```
Stock_Analize/
├── backend/              # 後端服務（Python）
│   ├── api/             # API 端點
│   ├── crawler/         # 資料抓取模組
│   ├── database/        # 資料庫模型與操作
│   ├── scheduler/       # 定時任務
│   └── services/        # 業務邏輯服務
├── frontend/            # 前端介面（Vue.js）
│   ├── src/
│   │   ├── components/  # Vue 組件
│   │   ├── views/       # 頁面視圖
│   │   ├── services/    # API 服務
│   │   └── router/      # 路由配置
└── docs/                # 文件
```

## 🛠️ 技術棧

### 後端
- **Python 3.10+**
- **FastAPI** - RESTful API 框架
- **SQLAlchemy** - ORM 資料庫操作
- **APScheduler** - 定時任務排程
- **yfinance** / **pandas** - 股票資料抓取與處理
- **SQLite/PostgreSQL** - 資料庫

### 前端
- **Vue 3** - 前端框架
- **Vite** - 建置工具
- **Chart.js** - 圖表視覺化（規劃中）
- **Tailwind CSS** - UI 樣式
- **Pinia** - 狀態管理
- **Axios** - HTTP 請求

## 📊 資料來源

### 免費 API 選項

1. **Yahoo Finance (yfinance)**
   - ✅ 免費、穩定
   - ✅ 支援台股、美股、全球股市
   - ✅ 提供歷史資料和即時報價
   - ⚠️ 有速率限制

2. **Alpha Vantage**（可選）
   - ✅ 免費層級（每月 500 次請求）
   - ✅ 提供技術指標 API
   - ⚠️ 需要 API Key
   - ⚠️ 免費層級有速率限制

3. **台灣證交所公開資料**（規劃中）
   - ✅ 完全免費
   - ✅ 官方資料來源
   - ⚠️ 僅限台股
   - ⚠️ 更新頻率較低

## 🚀 快速開始

### 方法一：使用啟動腳本（推薦）

```bash
cd Stock_Analize
./start.sh
```

系統會自動：
1. 檢查環境
2. 安裝依賴（如果需要的話）
3. 啟動後端和前端服務

訪問：**http://localhost:5173**

停止服務：
```bash
./stop.sh
```

### 方法二：手動啟動

#### 1. 設置後端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # 可選
python main.py
```

後端將在 `http://localhost:8000` 啟動

#### 2. 設置前端（新終端）

```bash
cd frontend
npm install
cp .env.example .env  # 可選
npm run dev
```

前端將在 `http://localhost:5173` 啟動

### 3. 訪問應用程式

開啟瀏覽器訪問：**http://localhost:5173**

## 📖 詳細文件

- [快速開始指南](./QUICK_START.md) - 最快速的上手指南
- [使用說明](./docs/使用說明.md) - 完整的使用說明
- [系統架構設計](./docs/架構設計.md) - 技術架構說明
- [API 文件](./docs/API文件.md) - API 端點詳細說明
- [資料庫設計](./docs/資料庫設計.md) - 資料庫結構說明
- [部署指南](./docs/部署指南.md) - 生產環境部署說明

## 🔧 配置說明

### 股票列表配置

在 `backend/config/stocks.json` 中設定要監控的股票（可選）。

### 定時任務配置

在 `backend/.env` 中設定抓取頻率：

```env
UPDATE_INTERVAL_MINUTES=5
TRADING_HOURS_ONLY=True
```

## 📝 開發計劃

### Phase 1: 基礎功能 ✅
- [x] 後端 API 架構
- [x] 資料抓取模組
- [x] 基礎儀表板介面
- [x] 股票列表顯示
- [x] 價格資訊顯示

### Phase 2: 進階功能 🔄
- [ ] 技術指標計算
- [ ] 歷史資料查詢優化
- [ ] 價格趨勢圖表
- [ ] 股票詳情頁面優化

### Phase 3: 優化與擴展 📋
- [ ] 資料快取機制
- [ ] 即時通知功能
- [ ] 多用戶支援
- [ ] 移動端適配

## 🆘 常見問題

### 如何新增股票？

1. 訪問 `http://localhost:8000/docs`
2. 找到 `POST /api/stocks` 端點
3. 點擊 "Try it out" 並輸入股票資訊

或使用 curl：
```bash
curl -X POST "http://localhost:8000/api/stocks" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "2330", "market": "TW", "name": "台積電"}'
```

### 資料何時更新？

系統會在以下時間自動更新：
- 開盤前：每天 08:50
- 交易時間：每 5 分鐘（可在 .env 設定）
- 收盤後：每天 15:30

### 遇到問題怎麼辦？

詳細說明請參考 [使用說明](./docs/使用說明.md) 的「常見問題」章節。

## 📄 授權

MIT License
