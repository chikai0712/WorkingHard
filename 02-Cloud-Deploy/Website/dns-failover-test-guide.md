# DNS 故障切換測試指南

## 📋 概述

本指南提供完整的 DNS 故障切換（Failover）測試方法，用於驗證多供應商 DNS 設定的可靠性。

---

## 🎯 測試目標

1. **驗證單一供應商 DNS 是否正常**
2. **觀察系統在 DNS 故障時的自動切換行為**
3. **使用 Wireshark 分析 DNS 查詢封包**

---

## 🔧 前置需求

### 必要工具

```bash
# macOS
brew install bind  # 安裝 dig 和 nslookup（通常已內建）

# 檢查工具
which nslookup
which dig
which tcpdump  # 用於封包捕獲（Wireshark 替代）
```

### 測試域名

- 域名：`www.clouddeployment168.site`
- AWS DNS：`205.251.197.44`
- Google DNS：`216.239.32.108`

---

## 🚀 快速開始

### 方法 1：使用自動化腳本（推薦）

```bash
# 1. 賦予執行權限
chmod +x dns-failover-test.sh

# 2. 執行測試（需要 sudo）
sudo ./dns-failover-test.sh www.clouddeployment168.site

# 或使用預設域名
sudo ./dns-failover-test.sh
```

### 方法 2：手動測試

參考下方「手動測試步驟」。

---

## 📝 測試階段

### 階段 1：基本功能測試

驗證每個 DNS 伺服器是否正常運作。

#### 1.1 測試 AWS DNS

```bash
nslookup www.clouddeployment168.site 205.251.197.44
```

**預期結果：**
```
Server:		205.251.197.44
Address:	205.251.197.44#53

Name:	www.clouddeployment168.site
Address: <IP 位址>
```

#### 1.2 測試 Google DNS

```bash
nslookup www.clouddeployment168.site 216.239.32.108
```

**預期結果：**
```
Server:		216.239.32.108
Address:	216.239.32.108#53

Name:	www.clouddeployment168.site
Address: <IP 位址>
```

#### 1.3 使用 dig 進行詳細測試

```bash
# 測試 AWS DNS
dig @205.251.197.44 www.clouddeployment168.site A +stats

# 測試 Google DNS
dig @216.239.32.108 www.clouddeployment168.site A +stats
```

**預期結果：**
- 兩個 DNS 都應該回傳相同的 A 記錄 IP
- 查詢時間應該在合理範圍內（< 100ms）

---

### 階段 2：故障切換測試

模擬 DNS 故障，觀察系統行為。

#### 2.1 使用 pfctl 封鎖 DNS（macOS）

```bash
# 1. 檢查當前 pfctl 狀態
sudo pfctl -sr

# 2. 封鎖 AWS DNS（模擬故障）
sudo pfctl -a custom -f - <<< 'block drop out quick proto udp from any to 205.251.197.44 port 53'

# 3. 測試被封鎖的 DNS（應該失敗）
nslookup www.clouddeployment168.site 205.251.197.44
# 預期：查詢逾時或失敗

# 4. 測試系統預設查詢（不指定 DNS）
nslookup www.clouddeployment168.site
# 預期：系統應該自動嘗試其他 DNS 伺服器

# 5. 解除封鎖
sudo pfctl -f /etc/pf.conf
```

#### 2.2 使用 Wireshark 觀察

**設定 Wireshark：**

1. 開啟 Wireshark
2. 選擇網路介面（例如：en0）
3. 過濾器輸入：`dns`
4. 開始捕獲

**執行測試：**

```bash
# 在終端機執行
nslookup www.clouddeployment168.site
```

**觀察重點：**

- **DNS 查詢封包**：查看查詢的目標 DNS 伺服器
- **DNS 回應封包**：查看回應的來源和內容
- **重傳（Retransmission）**：如果第一個 DNS 失敗，觀察是否有重傳
- **ICMP Destination Unreachable**：如果 DNS 被封鎖，會看到此封包

**預期行為：**

1. 系統先查詢第一個 DNS（例如：8.8.8.8）
2. 如果第一個 DNS 被封鎖，系統會等待逾時
3. 系統自動切換到第二個 DNS 伺服器
4. 第二個 DNS 回應成功

---

### 階段 3：進階測試

#### 3.1 測試 DNS 快取

```bash
# 查看 DNS 快取（macOS）
dscacheutil -q host -a name www.clouddeployment168.site

# 清除 DNS 快取（macOS）
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

#### 3.2 測試 DNS 解析順序

```bash
# 查看系統 DNS 設定
scutil --dns

# 查看當前使用的 DNS
networksetup -getdnsservers Wi-Fi  # Wi-Fi
networksetup -getdnsservers Ethernet  # 有線網路
```

#### 3.3 測試查詢時間

```bash
# 使用 dig 測試查詢時間
dig @205.251.197.44 www.clouddeployment168.site A +stats
dig @216.239.32.108 www.clouddeployment168.site A +stats

# 比較兩個 DNS 的響應時間
```

---

## 🔍 Wireshark 分析技巧

### 過濾器語法

```
# 只顯示 DNS 封包
dns

# 只顯示特定域名的 DNS 查詢
dns.qry.name == "www.clouddeployment168.site"

# 顯示 DNS 查詢和回應
dns.flags.response == 0  # 查詢
dns.flags.response == 1  # 回應

# 顯示特定 DNS 伺服器的封包
ip.addr == 205.251.197.44
ip.addr == 216.239.32.108
```

### 關鍵封包類型

1. **DNS Query**：客戶端發出的查詢
2. **DNS Response**：DNS 伺服器的回應
3. **DNS Retransmission**：查詢重傳（表示第一個查詢失敗）
4. **ICMP Destination Unreachable**：目標不可達（DNS 被封鎖時）

---

## 🐛 故障排除

### 問題 1：無法封鎖 DNS

**macOS：**
```bash
# 檢查 pfctl 是否啟用
sudo pfctl -s info

# 如果未啟用，需要先啟用
sudo pfctl -e
```

**Linux：**
```bash
# 使用 iptables
sudo iptables -A OUTPUT -d 205.251.197.44 -p udp --dport 53 -j DROP

# 解除封鎖
sudo iptables -D OUTPUT -d 205.251.197.44 -p udp --dport 53 -j DROP
```

### 問題 2：測試腳本無法執行

```bash
# 檢查權限
ls -la dns-failover-test.sh

# 賦予執行權限
chmod +x dns-failover-test.sh

# 使用 sudo 執行
sudo ./dns-failover-test.sh
```

### 問題 3：DNS 查詢一直失敗

1. **檢查網路連線**
   ```bash
   ping 8.8.8.8
   ```

2. **檢查 DNS 伺服器是否可達**
   ```bash
   ping 205.251.197.44
   ping 216.239.32.108
   ```

3. **檢查防火牆設定**
   ```bash
   # macOS
   sudo pfctl -sr
   
   # Linux
   sudo iptables -L -n
   ```

---

## 📊 測試結果解讀

### 正常情況

- ✅ 兩個 DNS 伺服器都能正常解析域名
- ✅ 查詢時間 < 100ms
- ✅ 回傳的 IP 位址一致

### 故障切換情況

- ✅ 第一個 DNS 被封鎖後，查詢失敗
- ✅ 系統自動切換到第二個 DNS
- ✅ 第二個 DNS 成功回應
- ✅ Wireshark 顯示重傳和切換行為

### 異常情況

- ❌ 兩個 DNS 都無法解析：可能是域名或網路問題
- ❌ 系統無法自動切換：可能是 DNS 設定問題
- ❌ 查詢時間過長：可能是網路延遲或 DNS 伺服器問題

---

## 💡 最佳實踐

### 1. 測試前準備

- 確保網路連線正常
- 關閉不必要的應用程式（減少網路干擾）
- 準備 Wireshark 用於封包分析

### 2. 測試時注意事項

- **只測試單一域名**：避免影響其他網路活動
- **快速測試**：封鎖 DNS 會影響網路，測試後立即解除
- **記錄結果**：保存測試日誌以便分析

### 3. 測試後清理

- 解除所有 DNS 封鎖
- 清除 DNS 快取（如果需要）
- 恢復正常網路設定

---

## 📚 相關資源

- [DNS 故障切換原理](https://en.wikipedia.org/wiki/DNS_failover)
- [Wireshark DNS 分析](https://www.wireshark.org/docs/wsug_html_chunked/ChWorkWithDisplayFilters.html)
- [macOS pfctl 文件](https://developer.apple.com/library/archive/documentation/Darwin/Reference/ManPages/man8/pfctl.8.html)

---

## ✅ 檢查清單

測試完成後，確認：

- [ ] 兩個 DNS 伺服器都能正常解析
- [ ] 故障切換測試成功
- [ ] Wireshark 捕獲到相關封包
- [ ] 所有 DNS 封鎖已解除
- [ ] 網路連線恢復正常

---

## 🎉 完成！

如果所有測試都通過，表示你的多供應商 DNS 設定是正確的，並且具備故障切換能力。

如有問題，請參考故障排除章節或查看測試腳本的輸出日誌。
