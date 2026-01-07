# 🚀 快速開始

## 一鍵啟動指南

### 第一步：設置後端

```bash
# 1. 進入後端目錄
cd Stock_Analize/backend

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 複製環境變數檔案
cp .env.example .env

# 4. 初始化資料庫並新增初始股票
python -c "from database.session import init_db; init_db()"
python scripts/add_stocks.py

# 5. 啟動後端服務
python main.py
```

**後端將運行在**：`http://localhost:8000`  
**API 文件**：`http://localhost:8000/docs`

---

### 第二步：設置前端（新終端視窗）

```bash
# 1. 進入前端目錄
cd Stock_Analize/frontend

# 2. 安裝依賴
npm install

# 3. 複製環境變數檔案
cp .env.example .env

# 4. 啟動前端開發伺服器
npm run dev
```

**前端將運行在**：`http://localhost:5173`

---

### 第三步：測試連線

1. **測試後端**：
   ```bash
   curl http://localhost:8000/health
   ```
   應該返回：`{"status": "healthy"}`

2. **測試前端**：
   開啟瀏覽器訪問 `http://localhost:5173`

3. **手動抓取資料**（可選）：
   ```bash
   cd Stock_Analize/backend
   python scripts/manual_update.py
   ```

---

## 🔍 驗證連線

### 後端 API 測試

```bash
# 1. 取得所有股票
curl http://localhost:8000/api/stocks

# 2. 取得特定股票（例如台積電）
curl http://localhost:8000/api/stocks/2330

# 3. 取得股票最新價格
curl http://localhost:8000/api/stocks/2330/price
```

### 前端連線測試

1. 開啟瀏覽器開發者工具（F12）
2. 切換到 **Network** 標籤
3. 重新載入頁面
4. 檢查是否有對 `/api/stocks` 的請求
5. 確認請求狀態為 `200 OK`

---

## ⚠️ 常見問題

### 問題 1：端口被占用

**錯誤**：`Address already in use`

**解決**：
- 修改 `backend/.env` 中的 `PORT=8000` 為其他端口（如 `8001`）
- 同時修改 `frontend/.env` 中的 `VITE_API_BASE_URL` 指向新端口

### 問題 2：模組找不到

**錯誤**：`ModuleNotFoundError`

**解決**：
```bash
# 確認在虛擬環境中
which python  # 應該指向 venv/bin/python

# 重新安裝依賴
pip install -r requirements.txt
```

### 問題 3：CORS 錯誤

**錯誤**：瀏覽器顯示 CORS 錯誤

**解決**：
確認 `backend/.env` 中的 `CORS_ORIGINS` 包含：
```
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## 📚 下一步

- 查看 [完整使用指南](./docs/快速開始指南.md)
- 閱讀 [API 文件](./docs/API文件.md)
- 了解 [系統架構](./docs/架構設計.md)

