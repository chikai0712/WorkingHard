# 🔧 問題排除指南

## 常見問題與解決方案

### 問題 1: 前端無法開啟 (http://localhost:5173)

**症狀**: 瀏覽器顯示「無法連接到此網站」

**可能原因與解決方法**:

1. **前端服務未啟動**
   ```bash
   cd Stock_Analize/frontend
   npm run dev
   ```

2. **端口被占用**
   ```bash
   # 檢查端口
   lsof -ti:5173
   
   # 如果被占用，可以修改 vite.config.js 中的端口號
   ```

3. **依賴未安裝**
   ```bash
   cd Stock_Analize/frontend
   npm install
   ```

---

### 問題 2: 後端無法啟動

**症狀**: 運行 `python main.py` 時出現錯誤

**可能原因與解決方法**:

1. **Python 版本問題** (需要 3.10+)
   ```bash
   python3 --version
   # 如果是 Python 3.13，可能需要更新某些套件版本
   ```

2. **依賴未安裝**
   ```bash
   cd Stock_Analize/backend
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **pandas/pydantic 版本不相容** (Python 3.13)
   - 已經在 requirements.txt 中更新為相容版本
   - 如果仍有問題，嘗試：
     ```bash
     pip install "pandas>=2.2.0" "pydantic>=2.10.0" --upgrade
     ```

---

### 問題 3: 前端無法連接到後端 API

**症狀**: 前端頁面顯示「無法連接」或 API 請求失敗

**解決方法**:

1. **確認後端正在運行**
   ```bash
   curl http://localhost:8000/health
   # 應該返回: {"status":"healthy"}
   ```

2. **檢查 CORS 設定**
   - 確認 `backend/.env` 中的 `CORS_ORIGINS` 包含前端 URL
   - 預設應該包含 `http://localhost:5173`

3. **檢查 API URL 設定**
   - 確認 `frontend/.env` 中的 `VITE_API_BASE_URL=http://localhost:8000/api`

---

### 問題 4: 資料庫錯誤

**症狀**: 啟動時出現資料庫相關錯誤

**解決方法**:

1. **SQLite 檔案權限問題**
   ```bash
   cd Stock_Analize/backend
   rm stock_data.db  # 刪除舊資料庫
   python main.py    # 會自動重新建立
   ```

2. **資料庫鎖定**
   - 確保沒有多個後端實例同時運行
   - 關閉所有後端進程後重新啟動

---

### 問題 5: 無法取得股票資料

**症狀**: 股票列表為空或顯示錯誤

**解決方法**:

1. **確認已新增股票**
   - 訪問 http://localhost:8000/docs
   - 使用 `POST /api/stocks` 端點新增股票

2. **檢查網路連線**
   - yfinance 需要網路連線
   - 確認可以訪問 yahoo.com

3. **檢查股票代號格式**
   - 台股：使用數字代號，如 "2330"
   - 美股：使用字母代號，如 "AAPL"

---

## 🔍 診斷步驟

### 步驟 1: 檢查服務狀態

```bash
# 檢查前端
curl http://localhost:5173

# 檢查後端
curl http://localhost:8000/health
```

### 步驟 2: 檢查日誌

```bash
# 後端日誌（如果使用啟動腳本）
tail -f Stock_Analize/logs/backend.log

# 前端日誌
tail -f Stock_Analize/logs/frontend.log
```

### 步驟 3: 檢查進程

```bash
# 檢查端口使用情況
lsof -ti:5173  # 前端
lsof -ti:8000  # 後端
```

---

## 💡 快速修復指令

### 完整重置

```bash
# 停止所有服務
./stop.sh  # 或手動 kill 進程

# 重新安裝依賴
cd backend && rm -rf venv && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && rm -rf node_modules && npm install

# 重新啟動
cd ../backend && source venv/bin/activate && python main.py &
cd ../frontend && npm run dev &
```

---

## 📞 取得協助

如果以上方法都無法解決問題，請：

1. 檢查終端錯誤訊息
2. 查看瀏覽器控制台（F12）
3. 檢查日誌檔案
4. 確認 Python 和 Node.js 版本符合要求

