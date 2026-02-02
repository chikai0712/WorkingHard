# Wireshark DNS 封包分析報告

## 📊 分析摘要

**測試時間範圍：** 21.997 秒 - 33.104 秒  
**測試域名：** `www.clouddeployment168.site`  
**結論：** ❌ **DNS 封鎖未生效，未觀察到故障切換行為**

---

## 🔍 關鍵 DNS 封包分析

### 1. AWS DNS (205.251.197.44) 查詢

| 封包編號 | 時間戳 | 來源 | 目標 | 協議 | 說明 |
|---------|--------|------|------|------|------|
| **584** | 21.997305 | 10.40.3.146 | 205.251.197.44 | DNS | **查詢** `www.clouddeployment168.site` A 記錄 |
| **585** | 22.041386 | 205.251.197.44 | 10.40.3.146 | DNS | **回應** A 記錄 = `44.202.226.49` ✅ |

**結果：** ✅ AWS DNS 查詢成功，延遲約 44ms

### 2. Google DNS (8.8.8.8) 查詢

| 封包編號 | 時間戳 | 來源 | 目標 | 協議 | 說明 |
|---------|--------|------|------|------|------|
| **684** | 22.063415 | 10.40.3.146 | 8.8.8.8 | DNS | **查詢** `www.clouddeployment168.site` A 記錄 |
| **791** | 22.097740 | 8.8.8.8 | 10.40.3.146 | DNS | **回應** A 記錄 = `44.202.226.49` ✅ |

**結果：** ✅ Google DNS 查詢成功，延遲約 34ms

---

## ❌ 未觀察到的現象（應出現但未出現）

### 1. **ICMP Destination Unreachable**
- **預期：** 如果 DNS 被封鎖，應該會看到 ICMP Type 3 (Destination Unreachable) 封包
- **實際：** ❌ 未發現任何 ICMP 錯誤封包

### 2. **DNS 重傳 (Retransmission)**
- **預期：** 如果第一個 DNS 查詢失敗，應該會看到重傳封包
- **實際：** ❌ 未發現任何 DNS 重傳封包

### 3. **DNS 查詢超時**
- **預期：** 如果 DNS 被封鎖，查詢應該會超時（通常 5-30 秒）
- **實際：** ✅ 所有查詢都在正常時間內得到回應

### 4. **自動切換到備用 DNS**
- **預期：** 如果第一個 DNS 失敗，系統應該自動切換到第二個 DNS
- **實際：** ❌ 兩個 DNS 查詢幾乎同時發生（間隔僅 6.5 秒），這是**並行查詢**而非故障切換

---

## 🔎 詳細時間線分析

```
時間軸：
├─ 21.997s: 查詢 AWS DNS (205.251.197.44)
├─ 22.041s: AWS DNS 回應成功 ✅
├─ 22.063s: 查詢 Google DNS (8.8.8.8)  ← 僅間隔 6.5 秒
└─ 22.098s: Google DNS 回應成功 ✅
```

**觀察：**
- 兩個 DNS 查詢時間非常接近（僅間隔 6.5 秒）
- 這表明系統在**並行查詢**兩個 DNS 伺服器，而非等待第一個失敗後再切換
- 這是正常的 DNS 解析行為，不是故障切換

---

## 🚨 問題診斷

### 為什麼 DNS 封鎖未生效？

根據之前的測試記錄，可能的原因：

1. **pfctl 規則未正確應用**
   - 規則可能沒有被正確載入到 pfctl
   - 規則語法可能有誤
   - 規則可能被其他規則覆蓋

2. **DNS 查詢使用了不同的協議或端口**
   - 如果使用 DoH (DNS-over-HTTPS)，封鎖 UDP 53 端口無效
   - 如果使用 DoT (DNS-over-TLS)，封鎖 UDP 53 端口無效

3. **DNS 快取**
   - 系統可能使用了快取的 DNS 結果
   - 即使封鎖了 DNS 伺服器，快取結果仍然可用

4. **多個網路介面**
   - 如果有多個網路介面，封鎖規則可能只應用到其中一個

---

## ✅ 驗證 DNS 封鎖是否生效的方法

### 方法 1：檢查 pfctl 規則

```bash
# 檢查規則是否存在
sudo pfctl -a custom -sr | grep 205.251.197.44

# 檢查所有規則
sudo pfctl -sr
```

### 方法 2：直接測試 DNS 查詢

```bash
# 測試被封鎖的 DNS 是否真的無法查詢
dig @205.251.197.44 www.clouddeployment168.site +time=2 +tries=1

# 如果封鎖生效，應該會：
# - 查詢超時
# - 返回 "connection timed out"
# - 或返回 "no servers could be reached"
```

### 方法 3：使用 tcpdump 即時監控

```bash
# 監控所有 DNS 流量
sudo tcpdump -i any -n port 53

# 如果封鎖生效，應該看不到任何發往 205.251.197.44:53 的封包
```

---

## 📋 建議的測試步驟

### 步驟 1：確認封鎖規則已應用

```bash
# 應用封鎖規則
echo 'block drop out quick proto udp from any to 205.251.197.44 port 53' | \
  sudo pfctl -a custom -f -

# 驗證規則
sudo pfctl -a custom -sr | grep 205.251.197.44
```

### 步驟 2：清除 DNS 快取

```bash
# macOS
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

### 步驟 3：測試 DNS 查詢

```bash
# 測試被封鎖的 DNS（應該失敗）
dig @205.251.197.44 www.clouddeployment168.site +time=2 +tries=1

# 測試未封鎖的 DNS（應該成功）
dig @8.8.8.8 www.clouddeployment168.site +time=2 +tries=1
```

### 步驟 4：使用 Wireshark 觀察

1. 開啟 Wireshark，過濾器：`dns or icmp`
2. 執行 `nslookup www.clouddeployment168.site`
3. 觀察是否出現：
   - ❌ ICMP Destination Unreachable
   - ❌ DNS 重傳
   - ✅ 查詢超時後切換到備用 DNS

---

## 🎯 預期的故障切換行為

如果 DNS 封鎖**成功**，應該觀察到：

1. **第一次查詢失敗：**
   ```
   查詢 → 205.251.197.44:53
   ↓
   封包被 pfctl 丟棄
   ↓
   等待超時（5-30 秒）
   ```

2. **ICMP 錯誤（可選）：**
   ```
   某些系統可能發送 ICMP Destination Unreachable
   ```

3. **自動切換到備用 DNS：**
   ```
   查詢超時後
   ↓
   系統自動切換到 8.8.8.8
   ↓
   查詢成功
   ```

4. **Wireshark 中應該看到：**
   - DNS 查詢到 205.251.197.44（無回應）
   - 等待一段時間（超時）
   - DNS 查詢到 8.8.8.8（成功回應）

---

## 📝 結論

根據本次 Wireshark 分析：

1. ✅ **兩個 DNS 伺服器都正常回應**
2. ❌ **未觀察到任何封鎖跡象**
3. ❌ **未觀察到故障切換行為**
4. ✅ **系統使用並行查詢而非故障切換**

**建議：**
- 重新檢查 pfctl 規則是否正確應用
- 確認 DNS 查詢使用的協議（UDP 53 vs DoH/DoT）
- 清除 DNS 快取後重新測試
- 使用 `tcpdump` 即時驗證封鎖是否生效

---

## 🔗 相關文件

- `Website/dns-failover-test.sh` - DNS 故障切換測試腳本
- `Website/pfctl-block-dns-guide.md` - pfctl 封鎖 DNS 指南
- `Website/封鎖DNS-手動步驟.md` - 手動封鎖 DNS 步驟
- `Website/wireshark-dns-guide.md` - Wireshark DNS 分析指南
