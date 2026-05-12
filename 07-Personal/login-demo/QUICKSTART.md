# 快速開始指南

## 1. 安裝依賴

```bash
cd /Users/ckchiu/Desktop/Project/login-demo
npm install
```

這會安裝：
- Express 服務器
- Puppeteer（壓測工具需要）

## 2. 啟動服務器

```bash
npm start
```

服務器會在 `http://localhost:3000` 啟動。

## 3. 訪問網站

打開瀏覽器訪問：http://localhost:3000

你會看到一個登入頁面，SentinelJS 會自動加載並收集指紋數據。

## 4. 測試登入

- 用戶名：任意（例如：`testuser`）
- 密碼：至少 6 個字符（例如：`testpass123`）

點擊登入按鈕，系統會：
1. 收集 SentinelJS 指紋數據
2. 發送到服務器
3. 顯示指紋哈希值

## 5. 使用壓測工具

在另一個終端窗口運行：

```bash
# 基本測試（10 次登入）
node load-test.js

# 更多測試（20 次登入，5 個並發）
node load-test.js --count 20 --concurrent 5

# 無頭模式（不顯示瀏覽器）
node load-test.js --count 50 --headless
```

## 6. 查看登入記錄

訪問 API 查看登入記錄：

```bash
# 查看登入記錄
curl http://localhost:3000/api/logs

# 查看指紋數據
curl http://localhost:3000/api/fingerprints
```

或在瀏覽器中訪問：
- http://localhost:3000/api/logs
- http://localhost:3000/api/fingerprints

## 常見問題

### Q: SentinelJS 加載失敗？
A: 檢查網絡連接，或修改 `public/index.html` 使用本地文件。

### Q: Puppeteer 安裝失敗？
A: 可能需要較長時間下載 Chromium，請耐心等待。

### Q: 端口被占用？
A: 修改 `server.js` 中的 `PORT` 變量，或使用環境變量：
```bash
PORT=3001 npm start
```

