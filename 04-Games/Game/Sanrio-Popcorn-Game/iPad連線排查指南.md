# 🔧 iPad 無法連線排查指南

## ✅ 檢查清單

### 1. 確認伺服器正在運行

在 Mac 的終端確認是否看到類似訊息：
```
Serving HTTP on 0.0.0.0 port 8888 (http://0.0.0.0:8888/) ...
```

如果沒有，請執行：
```bash
cd /Users/ckchiu/Desktop/Project/Game/Sanrio-Popcorn-Game
python3 -m http.server 8888 --bind 0.0.0.0
```

---

### 2. 確認 Mac 和 iPad 在同一個 Wi-Fi

**在 Mac 上檢查**：
- 點擊右上角 Wi-Fi 圖示
- 查看連接的網路名稱（例如：MyHome-WiFi）

**在 iPad 上檢查**：
- 設定 → Wi-Fi
- 確認連接的網路名稱與 Mac 相同

⚠️ **重要**：必須是同一個 Wi-Fi，不能是：
- Mac 用 Wi-Fi，iPad 用行動網路 ❌
- Mac 用 5GHz，iPad 用 2.4GHz（某些路由器會分開）❌

---

### 3. 獲取 Mac 的正確 IP 位址

**方法 A：使用終端**
```bash
# Wi-Fi
ipconfig getifaddr en0

# 乙太網路
ipconfig getifaddr en1
```

**方法 B：系統偏好設定**
1. 系統偏好設定 → 網路
2. 選擇 Wi-Fi（或乙太網路）
3. 查看「IP 位址」

**方法 C：快速查看所有 IP**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

應該會看到類似：
```
inet 192.168.1.100 netmask 0xffffff00 broadcast 192.168.1.255
```

您的 IP 就是：`192.168.1.100`

---

### 4. 在 iPad 上正確輸入網址

在 iPad 的 Safari 或 Chrome 瀏覽器輸入：

```
http://您的Mac的IP:8888
```

**範例**：
```
http://192.168.1.100:8888
```

⚠️ **常見錯誤**：
- ❌ `https://192.168.1.100:8888`（不要用 https）
- ❌ `192.168.1.100:8888`（缺少 http://）
- ❌ `http://localhost:8888`（localhost 只能在 Mac 上用）
- ✅ `http://192.168.1.100:8888`（正確）

---

## 🔥 macOS 防火牆檢查

### 檢查防火牆狀態

**步驟**：
1. 系統偏好設定 → 安全性與隱私
2. 點擊「防火牆」標籤
3. 查看防火牆是否開啟

### 如果防火牆開啟

**選項 A：允許 Python（推薦）**
1. 點擊「防火牆選項」
2. 找到 Python
3. 確保設定為「允許傳入連線」

**選項 B：暫時關閉防火牆（測試用）**
1. 點擊左下角鎖圖示解鎖
2. 點擊「關閉防火牆」
3. 測試 iPad 是否能連線
4. 測試完記得重新開啟

---

## 🧪 測試步驟

### 步驟 1：在 Mac 上測試

在 Mac 的瀏覽器輸入：
```
http://localhost:8888
```

如果能看到遊戲 → 伺服器正常 ✅

### 步驟 2：在 Mac 上用 IP 測試

在 Mac 的瀏覽器輸入：
```
http://您的IP:8888
```

如果能看到遊戲 → IP 正確 ✅

### 步驟 3：在 iPad 上測試

在 iPad 的瀏覽器輸入：
```
http://您的IP:8888
```

---

## 🔍 進階排查

### 檢查端口是否被佔用

在 Mac 終端執行：
```bash
lsof -i :8888
```

應該會看到 Python 正在使用 8888 端口

### 檢查網路連通性

在 Mac 終端執行：
```bash
# 查看 Mac 的 IP
ipconfig getifaddr en0

# 假設顯示 192.168.1.100
```

在 iPad 上：
1. 下載「Network Analyzer」或類似 App
2. Ping Mac 的 IP（192.168.1.100）
3. 如果能 Ping 通 → 網路正常

### 查看伺服器日誌

當 iPad 嘗試連線時，Mac 終端應該會顯示：
```
192.168.1.50 - - [08/Feb/2026 16:30:00] "GET / HTTP/1.1" 200 -
```

如果沒有任何訊息 → iPad 的請求沒有到達 Mac

---

## 🛠️ 常見問題解決方案

### 問題 1：iPad 顯示「無法連線到伺服器」

**可能原因**：
- Mac 和 iPad 不在同一個 Wi-Fi
- 防火牆阻擋
- IP 位址錯誤

**解決方案**：
1. 確認兩台設備在同一個 Wi-Fi
2. 暫時關閉 Mac 防火牆測試
3. 重新確認 IP 位址

### 問題 2：iPad 顯示「找不到伺服器」

**可能原因**：
- 伺服器沒有啟動
- 端口號錯誤

**解決方案**：
1. 確認 Mac 終端顯示伺服器正在運行
2. 確認網址包含正確的端口號（:8888）

### 問題 3：iPad 一直轉圈圈

**可能原因**：
- 網路速度慢
- 伺服器負載過高

**解決方案**：
1. 重新整理頁面
2. 重啟伺服器
3. 檢查 Wi-Fi 訊號強度

### 問題 4：某些路由器有「AP 隔離」功能

**症狀**：
- Mac 能訪問遊戲
- iPad 無法訪問

**解決方案**：
1. 登入路由器管理介面
2. 找到「AP 隔離」或「Client Isolation」設定
3. 關閉此功能

---

## 📋 完整檢查清單

請依序檢查：

- [ ] 伺服器正在運行（Mac 終端有訊息）
- [ ] Mac 和 iPad 連接同一個 Wi-Fi
- [ ] 已獲取 Mac 的正確 IP 位址
- [ ] 在 Mac 上能用 IP 訪問（http://IP:8888）
- [ ] Mac 防火牆允許 Python
- [ ] iPad 輸入正確網址（http://IP:8888）
- [ ] 路由器沒有開啟 AP 隔離

---

## 🆘 快速解決方案

### 方案 1：使用不同端口

```bash
# 停止當前伺服器（Ctrl+C）
# 使用不同端口
python3 -m http.server 3000 --bind 0.0.0.0

# iPad 訪問：http://IP:3000
```

### 方案 2：重啟網路

**在 Mac 上**：
1. 關閉 Wi-Fi
2. 等待 5 秒
3. 重新開啟 Wi-Fi

**在 iPad 上**：
1. 設定 → Wi-Fi
2. 點擊已連接的網路旁的 (i)
3. 點擊「忘記此網路」
4. 重新連接

### 方案 3：使用 USB 連線（最後手段）

如果 Wi-Fi 始終無法連線，可以：
1. 用 USB 線連接 iPad 和 Mac
2. 在 Mac 上開啟「個人熱點」
3. iPad 透過 USB 連線到 Mac
4. 使用 Mac 的熱點 IP 訪問

---

## 💡 測試命令

在 Mac 終端執行以下命令，將結果告訴我：

```bash
# 1. 查看 IP
echo "=== Mac IP 位址 ==="
ipconfig getifaddr en0

# 2. 查看伺服器狀態
echo "=== 伺服器狀態 ==="
lsof -i :8888

# 3. 查看防火牆狀態
echo "=== 防火牆狀態 ==="
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

---

**請告訴我：**
1. Mac 的 IP 位址是什麼？
2. iPad 輸入的網址是什麼？
3. iPad 顯示什麼錯誤訊息？
4. Mac 終端是否有顯示 iPad 的連線請求？

我會根據您的回答幫您解決問題！🔧✨

