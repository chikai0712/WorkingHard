# 🚀 快速開始指南

## 步驟 1：設置後端

```bash
# 進入後端目錄
cd Stock_Analize/backend

# 安裝 Python 依賴
pip install -r requirements.txt

# 複製環境變數檔案（如果還沒有）
# cp .env.example .env

# 啟動後端服務
python main.py
```

後端將在 `http://localhost:8000` 啟動 ✅

---

## 步驟 2：設置前端（新的終端視窗）

```bash
# 進入前端目錄
cd Stock_Analize/frontend

# 安裝 Node.js 依賴
npm install

# 複製環境變數檔案（如果還沒有）
# cp .env.example .env

# 啟動前端開發伺服器
npm run dev
```

前端將在 `http://localhost:5173` 啟動 ✅

---

## 步驟 3：訪問應用程式

開啟瀏覽器，訪問：**http://localhost:5173**

---

## 步驟 4：新增股票（可選）

### 方法一：使用 API 文件頁面

1. 訪問 `http://localhost:8000/docs`
2. 找到 `POST /api/stocks`
3. 點擊 "Try it out"
4. 輸入範例資料：
   ```json
   {
     "symbol": "2330",
     "market": "TW",
     "name": "台積電",
     "industry": "半導體"
   }
   ```
5. 點擊 "Execute"

### 方法二：使用 curl

```bash
curl -X POST "http://localhost:8000/api/stocks" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "2330",
    "market": "TW",
    "name": "台積電"
  }'
```

---

## ✅ 完成！

現在您可以：
- 在儀表板查看股票列表
- 點擊股票查看詳細資訊
- 系統會自動每 5 分鐘更新資料（交易時間）

---

## 🆘 遇到問題？

- **後端無法啟動**：確認 Python 版本（需要 3.10+）和依賴已安裝
- **前端無法連接**：確認後端服務正在運行（訪問 `http://localhost:8000/health`）
- **沒有資料**：記得先新增股票

詳細說明請參考 [使用說明](./docs/使用說明.md)

