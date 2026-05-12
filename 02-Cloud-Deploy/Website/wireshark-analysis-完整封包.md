# Wireshark 完整封包分析

## 📊 對 `www.clouddeployment168.site` 的 DNS 查詢

從你提供的封包中，找到以下 DNS 查詢：

| 封包 | 時間 | 動作 | DNS 伺服器 | 回應時間 | 狀態 |
|------|------|------|-----------|---------|------|
| 423 | 24.377s | 查詢 | 205.251.197.44 (AWS) | 24.538s (160ms) | ✅ 成功 |
| 425 | 24.538s | 回應 | 205.251.197.44 (AWS) | - | ✅ 成功 |
| 482 | 29.449s | 查詢 | 205.251.197.44 (AWS) | 29.501s (52ms) | ✅ 成功 |
| 483 | 29.501s | 回應 | 205.251.197.44 (AWS) | - | ✅ 成功 |
| 584 | 29.532s | 查詢 | 8.8.8.8 (Google) | 29.698s (166ms) | ✅ 成功 |
| 696 | 29.698s | 回應 | 8.8.8.8 (Google) | - | ✅ 成功 |

---

## 🔍 關鍵觀察

### ✅ 發現

1. **所有 DNS 查詢都成功**
   - AWS DNS (205.251.197.44)：160ms 和 52ms 回應
   - Google DNS (8.8.8.8)：166ms 回應

2. **查詢時間間隔**
   - 第一次：24.377s (AWS)
   - 第二次：29.449s (AWS) = **5 秒後**
   - 第三次：29.532s (Google) = **只差 83ms**（幾乎同時）

3. **沒有故障切換跡象**
   - 沒有 ICMP 錯誤
   - 沒有重傳
   - 沒有查詢失敗

### ❌ 沒有看到的（關鍵問題）

1. **ICMP Destination Unreachable**
   - **結論：DNS 沒有被封鎖，或封鎖未生效**

2. **時間延遲**
   - 兩個查詢只差 83ms
   - **結論：並行查詢，不是故障切換**

3. **重傳或錯誤**
   - 所有查詢都成功
   - **結論：沒有故障，所以沒有切換**

---

## 🎯 結論

### 主要問題

**DNS 封鎖沒有生效！**

證據：
1. AWS DNS (205.251.197.44) 成功回應（52ms 和 160ms）
2. 沒有 ICMP 錯誤
3. 查詢時間差只有 83ms（並行查詢）

### 這不是故障切換

真正的故障切換應該看到：
- ICMP 錯誤（表示被封鎖）
- 明顯的時間延遲（1-5 秒）
- 查詢失敗後切換到其他 DNS

你的封包顯示：
- 所有查詢都成功
- 沒有時間延遲
- 並行查詢，不是故障切換

---

## 🔧 解決方案

### 步驟 1：確認封鎖規則是否存在

```bash
# 檢查規則
sudo pfctl -a custom -sr | grep 205.251.197.44

# 如果沒有輸出，表示規則不存在
```

### 步驟 2：如果規則不存在，重新封鎖

```bash
# 方法 1：使用 anchor
echo 'block drop out quick proto udp from any to 205.251.197.44 port 53' | \
    sudo pfctl -a custom -f -

# 方法 2：如果方法 1 失敗，使用主規則集
(sudo pfctl -sr; \
 echo 'block drop out quick proto udp from any to 205.251.197.44 port 53') | \
    sudo pfctl -f -
```

### 步驟 3：驗證封鎖生效（必須失敗！）

```bash
# 測試封鎖
dig @205.251.197.44 www.clouddeployment168.site +time=2 +tries=1

# 如果成功，表示封鎖未生效
# 如果失敗或超時，表示封鎖生效
```

**重要：** 如果 `dig` 仍然成功，封鎖未生效，需要檢查 pfctl 設定。

### 步驟 4：正確的測試流程

```bash
# 1. 封鎖 DNS
echo 'block drop out quick proto udp from any to 205.251.197.44 port 53' | \
    sudo pfctl -a custom -f -

# 2. 驗證規則存在
sudo pfctl -a custom -sr | grep 205.251.197.44
# 必須看到規則！

# 3. 測試封鎖（必須失敗！）
dig @205.251.197.44 www.clouddeployment168.site +time=2 +tries=1
# 如果成功，封鎖未生效，停止測試，檢查問題

# 4. 清除快取
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

# 5. 開啟 Wireshark，過濾器：dns || icmp

# 6. 執行查詢（不指定 DNS）
nslookup www.clouddeployment168.site
```

---

## 📊 預期結果 vs 實際結果

### 預期（故障切換）

```
0.000s → 查詢 AWS DNS (205.251.197.44)
0.001s ← ICMP Destination Unreachable（被封鎖）
2.000s → 查詢 Google DNS (8.8.8.8) [明顯延遲]
2.050s ← 成功回應
```

### 實際（你的封包）

```
24.377s → 查詢 AWS DNS (205.251.197.44)
24.538s ← AWS DNS 成功回應（160ms，沒有 ICMP 錯誤）
29.449s → 查詢 AWS DNS (205.251.197.44)
29.501s ← AWS DNS 成功回應（52ms）
29.532s → 查詢 Google DNS (8.8.8.8) [只差 83ms，並行查詢]
29.698s ← Google DNS 成功回應（166ms）
```

**差異：**
- ❌ 沒有 ICMP 錯誤（表示沒有被封鎖）
- ❌ 沒有時間延遲（表示並行查詢，不是故障切換）
- ❌ 所有查詢都成功（表示沒有故障）

---

## 🐛 故障排除

### 問題：規則存在但封鎖未生效

**可能原因：**
- pfctl 規則語法錯誤
- 規則順序問題
- 系統設定覆蓋規則

**解決方法：**
```bash
# 1. 檢查所有規則
sudo pfctl -sr

# 2. 檢查是否有允許規則在封鎖規則之前
sudo pfctl -sr | grep -A 5 -B 5 205.251.197.44

# 3. 使用更強制的規則
echo 'block drop out quick proto udp from any to 205.251.197.44 port 53' | \
    sudo pfctl -a custom -f -

# 4. 重新載入
sudo pfctl -f /etc/pf.conf 2>/dev/null || true
echo 'block drop out quick proto udp from any to 205.251.197.44 port 53' | \
    sudo pfctl -a custom -f -
```

---

## ✅ 檢查清單

在執行測試前，必須確認：

- [ ] **規則存在**：`sudo pfctl -a custom -sr | grep 205.251.197.44`
- [ ] **封鎖生效**：`dig @205.251.197.44` **必須失敗**
- [ ] **DNS 快取已清除**：`sudo dscacheutil -flushcache`
- [ ] **Wireshark 已開啟**：過濾器 `dns || icmp`
- [ ] **查詢在封鎖後執行**：先封鎖，再查詢

**如果 `dig @205.251.197.44` 仍然成功，不要繼續測試，先解決封鎖問題！**

---

## 💡 下一步行動

1. **立即檢查**：執行 `dig @205.251.197.44 www.clouddeployment168.site +time=2 +tries=1`
   - 如果成功 → 封鎖未生效，需要解決
   - 如果失敗 → 封鎖生效，可以繼續測試

2. **如果封鎖未生效**：
   - 檢查規則是否存在
   - 檢查 pfctl 狀態
   - 嘗試不同的封鎖方法

3. **如果封鎖生效**：
   - 清除快取
   - 重新測試
   - 在 Wireshark 中應該看到 ICMP 錯誤

---

## 🎯 總結

從你的封包來看：

1. **DNS 沒有被封鎖**（所有查詢都成功）
2. **系統使用並行查詢**（83ms 間隔，不是故障切換）
3. **沒有故障切換行為**（沒有 ICMP 錯誤，沒有時間延遲）

**關鍵問題：封鎖未生效**

**解決方法：**
1. 確認規則存在
2. 驗證封鎖生效（`dig` 必須失敗）
3. 如果失敗，檢查 pfctl 設定
4. 重新測試

請先執行 `dig @205.251.197.44 www.clouddeployment168.site +time=2 +tries=1`，告訴我結果，我會幫你進一步診斷。
