# DNS 故障切換分析指南

## 📊 從你的 Wireshark 封包分析

根據你提供的 Wireshark 封包，我發現了以下問題：

### 🔍 觀察結果

1. **同時查詢多個 DNS**
   - 系統同時查詢 8.8.8.8、205.251.197.44、216.239.32.108
   - 這不是故障切換，而是**並行查詢**

2. **沒有真正的故障切換**
   - 所有 DNS 查詢都成功回應
   - 沒有看到重傳（Retransmission）
   - 沒有看到 ICMP 錯誤（表示沒有被封鎖）

3. **查詢模式**
   ```
   112.05s → 8.8.8.8 (成功)
   113.07s → 205.251.197.44 (成功)
   114.11s → 216.239.32.108 (成功)
   ```
   這是**並行查詢**，不是故障切換。

---

## ❓ 為什麼沒有故障切換？

### 可能原因

1. **DNS 沒有被封鎖**
   - 測試腳本的封鎖可能沒有生效
   - pfctl 規則可能沒有正確應用

2. **系統使用並行查詢**
   - macOS 可能同時查詢所有配置的 DNS
   - 不是順序查詢，所以看不到切換

3. **DNS 快取**
   - 第一次查詢成功後，結果被快取
   - 後續查詢直接使用快取，不查詢 DNS

---

## 🔧 如何驗證故障切換

### 方法 1：確認封鎖是否生效

```bash
# 檢查 pfctl 規則
sudo pfctl -sr | grep -E "(205.251.197.44|216.239.32.108)"

# 應該看到類似：
# block drop out quick proto udp from any to 205.251.197.44 port 53
```

### 方法 2：測試封鎖後的查詢

```bash
# 1. 封鎖 AWS DNS
sudo pfctl -a custom -f - <<< 'block drop out quick proto udp from any to 205.251.197.44 port 53'

# 2. 清除 DNS 快取
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

# 3. 查詢（應該失敗或切換）
nslookup www.clouddeployment168.site

# 4. 在 Wireshark 觀察：
#    - 應該看到查詢 205.251.197.44 失敗
#    - 應該看到 ICMP Destination Unreachable
#    - 應該看到系統切換到其他 DNS
```

### 方法 3：使用 dig 測試（更精確）

```bash
# 清除快取
sudo dscacheutil -flushcache

# 測試第一個 DNS（應該失敗）
dig @205.251.197.44 www.clouddeployment168.site +time=2

# 測試系統自動選擇（應該切換到其他 DNS）
dig www.clouddeployment168.site +time=5
```

---

## 🎯 正確的故障切換應該看到什麼？

### 在 Wireshark 中應該看到：

1. **第一次查詢（被封鎖的 DNS）**
   ```
   Frame X: DNS Query (你的 IP -> 205.251.197.44)
   Frame X+1: ICMP Destination Unreachable (205.251.197.44 -> 你的 IP)
   ```

2. **重傳（系統重試）**
   ```
   Frame X+2: DNS Query Retransmission (你的 IP -> 205.251.197.44)
   ```

3. **切換到第二個 DNS**
   ```
   Frame X+3: DNS Query (你的 IP -> 216.239.32.108)
   Frame X+4: DNS Response (216.239.32.108 -> 你的 IP) [成功]
   ```

4. **時間間隔**
   - 第一次查詢失敗到切換：通常 1-3 秒
   - 如果看到立即切換，可能是並行查詢

---

## 🔍 分析你的封包

從你的封包時間戳來看：

```
112.05s → 8.8.8.8 (查詢)
112.13s → 8.8.8.8 (回應，35ms)
113.07s → 205.251.197.44 (查詢)
113.11s → 205.251.197.44 (回應，39ms)
114.11s → 216.239.32.108 (查詢)
114.16s → 216.239.32.108 (回應，50ms)
```

**分析：**
- 所有查詢都成功（沒有失敗）
- 查詢間隔約 1 秒（不是故障切換，而是順序測試）
- 沒有看到 ICMP 錯誤（表示沒有被封鎖）
- 沒有看到重傳（表示沒有超時）

**結論：** 這不是故障切換測試，而是正常的 DNS 查詢測試。

---

## ✅ 如何進行真正的故障切換測試

### 步驟 1：確保封鎖生效

```bash
# 1. 封鎖 AWS DNS
sudo pfctl -a custom -f - <<< 'block drop out quick proto udp from any to 205.251.197.44 port 53'

# 2. 驗證封鎖
sudo pfctl -sr | grep 205.251.197.44
# 應該看到封鎖規則

# 3. 測試封鎖是否生效
dig @205.251.197.44 www.clouddeployment168.site +time=2
# 應該失敗或超時
```

### 步驟 2：清除快取並測試

```bash
# 清除 DNS 快取
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

# 開啟 Wireshark，過濾器：dns || icmp

# 執行查詢（不指定 DNS，讓系統自動選擇）
nslookup www.clouddeployment168.site
```

### 步驟 3：觀察 Wireshark

**應該看到：**

1. **查詢被封鎖的 DNS**
   - DNS Query → 205.251.197.44
   - ICMP Destination Unreachable ← 205.251.197.44

2. **等待/重傳**
   - DNS Query Retransmission → 205.251.197.44（可選）

3. **切換到其他 DNS**
   - DNS Query → 216.239.32.108 或 8.8.8.8
   - DNS Response ← 成功回應

4. **時間間隔**
   - 從第一次查詢到切換：應該有明顯延遲（1-5 秒）

---

## 🐛 如果還是沒有切換

### 可能原因和解決方法

1. **macOS 使用並行查詢**
   - macOS 可能同時查詢所有 DNS，不等待第一個失敗
   - **解決方法：** 只配置一個 DNS，測試故障切換

2. **DNS 快取**
   - 結果被快取，不查詢 DNS
   - **解決方法：** 每次測試前清除快取

3. **封鎖未生效**
   - pfctl 規則沒有正確應用
   - **解決方法：** 檢查規則，使用更強制的方法

4. **系統 DNS 設定**
   - 系統可能配置了多個 DNS，使用並行查詢
   - **解決方法：** 檢查 `scutil --dns`，只保留一個 DNS

---

## 📝 改進的測試方法

### 方法 1：只配置一個 DNS

```bash
# 1. 查看當前 DNS 設定
scutil --dns | grep nameserver

# 2. 在系統設定中，只保留一個 DNS（例如：205.251.197.44）

# 3. 封鎖這個 DNS
sudo pfctl -a custom -f - <<< 'block drop out quick proto udp from any to 205.251.197.44 port 53'

# 4. 清除快取
sudo dscacheutil -flushcache

# 5. 測試（應該切換到系統預設或其他 DNS）
nslookup www.clouddeployment168.site
```

### 方法 2：使用測試腳本（改進版）

執行改進後的測試腳本，它會：
1. 確認封鎖生效
2. 清除快取
3. 測試系統切換
4. 在 30 秒期間多次測試

---

## 💡 建議

1. **確認封鎖生效**：使用 `pfctl -sr` 檢查規則
2. **清除快取**：每次測試前清除 DNS 快取
3. **觀察時間**：故障切換應該有明顯的時間延遲
4. **使用 Wireshark**：觀察 ICMP 錯誤和重傳

---

## 🎯 下一步

1. 確認封鎖規則是否生效
2. 清除 DNS 快取
3. 重新執行測試
4. 在 Wireshark 中觀察 ICMP 錯誤和切換行為

如果還是沒有看到切換，可能是 macOS 的並行查詢機制，需要調整測試方法。
