# 封鎖 DNS - 手動步驟（規則不存在時）

## ❌ 問題診斷

從你的輸出可以看到：
```
sudo pfctl -a custom -sr | grep 205.251.197.44
（沒有輸出）
```

**結論：規則不存在，所以封鎖未生效**

---

## ✅ 解決方案

### 步驟 1：確保 pfctl 已啟用

```bash
# 檢查狀態
sudo pfctl -si | grep Status

# 如果未啟用，啟用它
sudo pfctl -e
```

### 步驟 2：封鎖 DNS（使用 anchor）

```bash
# 封鎖 DNS
echo 'block drop out quick proto udp from any to 205.251.197.44 port 53' | \
    sudo pfctl -a custom -f -

# 驗證規則存在
sudo pfctl -a custom -sr | grep 205.251.197.44
# 應該看到：block drop out quick proto udp from any to 205.251.197.44 port 53
```

### 步驟 3：如果 anchor 方法失敗，使用主規則集

```bash
# 添加到主規則集（保留現有規則）
(sudo pfctl -sr; \
 echo 'block drop out quick proto udp from any to 205.251.197.44 port 53') | \
    sudo pfctl -f -

# 驗證規則存在
sudo pfctl -sr | grep 205.251.197.44
# 應該看到規則
```

### 步驟 4：驗證封鎖生效（必須失敗！）

```bash
# 測試封鎖
dig @205.251.197.44 www.clouddeployment168.site +time=2 +tries=1

# 預期結果：
# - 如果成功 → 封鎖未生效，需要檢查
# - 如果失敗或超時 → 封鎖生效 ✅
```

---

## 🔧 完整測試流程

### 1. 封鎖 DNS

```bash
# 方法 A：使用 anchor（推薦）
echo 'block drop out quick proto udp from any to 205.251.197.44 port 53' | \
    sudo pfctl -a custom -f -

# 方法 B：如果方法 A 失敗
(sudo pfctl -sr; \
 echo 'block drop out quick proto udp from any to 205.251.197.44 port 53') | \
    sudo pfctl -f -
```

### 2. 驗證規則存在

```bash
# 檢查 anchor
sudo pfctl -a custom -sr | grep 205.251.197.44

# 或檢查主規則集
sudo pfctl -sr | grep 205.251.197.44

# 必須看到規則！
```

### 3. 測試封鎖（必須失敗！）

```bash
dig @205.251.197.44 www.clouddeployment168.site +time=2 +tries=1

# 如果成功，表示封鎖未生效，停止測試
# 如果失敗或超時，表示封鎖生效，繼續
```

### 4. 清除 DNS 快取

```bash
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

### 5. 開啟 Wireshark

- 過濾器：`dns || icmp`
- 開始捕獲

### 6. 執行查詢

```bash
nslookup www.clouddeployment168.site
```

### 7. 在 Wireshark 中應該看到

1. DNS Query → 205.251.197.44
2. ICMP Destination Unreachable ← 205.251.197.44（關鍵！）
3. DNS Query → 8.8.8.8（1-5 秒後）
4. DNS Response ← 成功回應

---

## 🐛 如果還是失敗

### 檢查項目

1. **pfctl 狀態**
   ```bash
   sudo pfctl -si
   # 應該顯示 Status: Enabled
   ```

2. **所有規則**
   ```bash
   sudo pfctl -sr
   # 查看是否有其他規則影響
   ```

3. **規則語法**
   ```bash
   # 正確語法
   block drop out quick proto udp from any to 205.251.197.44 port 53
   ```

4. **測試封鎖**
   ```bash
   dig @205.251.197.44 www.clouddeployment168.site +time=2 +tries=1
   # 必須失敗！
   ```

---

## 💡 使用腳本

```bash
# 使用提供的腳本
sudo ~/Desktop/Project/Website/正確封鎖DNS.sh 205.251.197.44
```

腳本會自動：
1. 確保 pfctl 已啟用
2. 嘗試 anchor 方法
3. 如果失敗，嘗試主規則集
4. 驗證封鎖是否生效

---

## ✅ 檢查清單

執行測試前，必須確認：

- [ ] **pfctl 已啟用**：`sudo pfctl -si | grep Status`
- [ ] **規則存在**：`sudo pfctl -a custom -sr | grep 205.251.197.44`
- [ ] **封鎖生效**：`dig @205.251.197.44` **必須失敗**
- [ ] **DNS 快取已清除**：`sudo dscacheutil -flushcache`
- [ ] **Wireshark 已開啟**：過濾器 `dns || icmp`

**如果 `dig @205.251.197.44` 仍然成功，不要繼續測試，先解決封鎖問題！**
