# Globalping API 手動測試指南

## 問題診斷

你的監控頁面顯示「還沒有資料」是因為：
- **網絡限制** - 當前環境無法訪問外部 API
- **代理阻止** - 公司代理返回 403 Forbidden

## 測試方法

### 方法 1：使用 Python 腳本（推薦）

在允許外網訪問的環境中運行：

```bash
cd /Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1
python test_api_manual.py
```

**預期輸出：**
- ✅ 如果 Token 有效，會顯示 API 額度信息
- ✅ 會成功創建一個測量
- ✅ 會獲取最近的測量結果

### 方法 2：使用 Bash 腳本

```bash
cd /Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1
bash test_api_manual.sh
```

### 方法 3：手動 curl 命令

```bash
# 測試 API 連接
curl -X GET https://api.globalping.io/v1/limits \
  -H "Authorization: Bearer uh5vlg4ttg3v5gwby5zgtqrciimahql5" \
  -H "Content-Type: application/json"

# 創建測量
curl -X POST https://api.globalping.io/v1/measurements \
  -H "Authorization: Bearer uh5vlg4ttg3v5gwby5zgtqrciimahql5" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "http",
    "target": "example.com",
    "inProgressUpdates": false,
    "options": {"method": "HEAD"}
  }'
```

## 測試結果解釋

### ✅ 成功情況
```
Status Code: 200
Body: {
  "rateLimit": {
    "measurements": {
      "create": {
        "remaining": 1000,
        "reset": 3600
      }
    }
  }
}
```
→ Token 有效，API 可以使用

### ❌ 失敗情況
```
Status Code: 403
Body: {"error": "Unauthorized"}
```
→ Token 無效或已過期

```
Status Code: 0 (連接超時)
```
→ 網絡無法訪問 API

## 後續步驟

### 如果測試成功 ✅
1. 在允許外網的環境中運行應用
2. 或配置代理繞過
3. 應用會自動開始檢測並填充數據

### 如果測試失敗 ❌
1. **檢查 Token** - 訪問 https://app.globalping.io 生成新 Token
2. **檢查網絡** - 確保可以訪問外部 API
3. **檢查代理** - 配置代理繞過或使用 VPN

## 配置代理繞過（可選）

編輯 `.env` 文件：

```bash
# 添加以下行
NO_PROXY=127.0.0.1,::1,localhost,api.globalping.io,*.globalping.io
```

然後重啟應用。

## 快速診斷命令

```bash
# 檢查網絡連接
ping api.globalping.io

# 檢查 DNS
nslookup api.globalping.io

# 檢查代理設置
echo $HTTP_PROXY
echo $HTTPS_PROXY
echo $NO_PROXY
```

---

**需要幫助？** 運行測試腳本後告訴我結果，我可以進一步診斷。
