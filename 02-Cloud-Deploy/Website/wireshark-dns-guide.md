# Wireshark DNS 分析指南

## 📋 概述

本指南說明如何使用 Wireshark 觀察和分析 DNS 故障切換行為。

---

## 🔧 安裝 Wireshark

### macOS

```bash
brew install --cask wireshark
```

### Linux

```bash
# Ubuntu/Debian
sudo apt-get install wireshark

# RHEL/CentOS
sudo yum install wireshark
```

### Windows

從 [Wireshark 官網](https://www.wireshark.org/download.html) 下載安裝程式。

---

## 🚀 快速開始

### 步驟 1：開啟 Wireshark

1. 開啟 Wireshark
2. 選擇網路介面（例如：`en0` 或 `Wi-Fi`）
3. 點擊「開始捕獲」

### 步驟 2：設定過濾器

在過濾器欄位輸入：

```
dns
```

這會只顯示 DNS 相關的封包。

### 步驟 3：執行 DNS 查詢

在終端機執行：

```bash
nslookup www.clouddeployment168.site
```

### 步驟 4：觀察封包

在 Wireshark 中，你會看到：

- **DNS Query**：客戶端發出的查詢
- **DNS Response**：DNS 伺服器的回應

---

## 🔍 進階過濾器

### 基本過濾器

```
# 只顯示 DNS 封包
dns

# 只顯示特定域名的查詢
dns.qry.name == "www.clouddeployment168.site"

# 只顯示 DNS 查詢（不顯示回應）
dns.flags.response == 0

# 只顯示 DNS 回應
dns.flags.response == 1
```

### 進階過濾器

```
# 顯示特定 DNS 伺服器的封包
ip.addr == 205.251.197.44
ip.addr == 216.239.32.108

# 顯示 DNS 查詢和特定伺服器的回應
dns && (ip.src == 205.251.197.44 || ip.dst == 205.251.197.44)

# 顯示 DNS 重傳（表示查詢失敗）
dns.flags.retransmission == 1

# 顯示 DNS 錯誤回應
dns.flags.rcode != 0
```

### 組合過濾器

```
# 顯示特定域名的查詢和所有相關回應
dns.qry.name == "www.clouddeployment168.site" || (dns.resp.name == "www.clouddeployment168.site")

# 顯示 UDP 53 埠的所有封包（DNS）
udp.port == 53

# 顯示 DNS 查詢和 ICMP 錯誤（DNS 被封鎖時）
dns || (icmp && icmp.type == 3)
```

---

## 📊 關鍵封包類型

### 1. DNS Query（查詢）

**特徵：**
- `dns.flags.response == 0`
- 包含 `dns.qry.name`（查詢的域名）
- 來源 IP 是你的電腦
- 目標 IP 是 DNS 伺服器

**範例：**
```
Frame 123: DNS Query for www.clouddeployment168.site
Source: 192.168.1.100
Destination: 8.8.8.8
Protocol: DNS
Query: www.clouddeployment168.site A
```

### 2. DNS Response（回應）

**特徵：**
- `dns.flags.response == 1`
- 包含 `dns.resp.name`（回應的域名）
- 包含 `dns.a`（A 記錄 IP）
- 來源 IP 是 DNS 伺服器
- 目標 IP 是你的電腦

**範例：**
```
Frame 124: DNS Response for www.clouddeployment168.site
Source: 8.8.8.8
Destination: 192.168.1.100
Protocol: DNS
Response: www.clouddeployment168.site A 1.2.3.4
```

### 3. DNS Retransmission（重傳）

**特徵：**
- `dns.flags.retransmission == 1`
- 表示第一個查詢沒有收到回應
- 系統自動重傳查詢

**意義：**
- 第一個 DNS 伺服器可能故障或被封鎖
- 系統正在嘗試重新查詢

### 4. ICMP Destination Unreachable

**特徵：**
- `icmp.type == 3`
- 出現在 DNS 被封鎖時
- 表示封包無法到達目標

**意義：**
- DNS 伺服器被封鎖或不可達
- 系統會嘗試其他 DNS 伺服器

---

## 🎯 故障切換測試場景

### 場景 1：正常查詢

**步驟：**

1. 開啟 Wireshark，過濾器：`dns`
2. 執行：`nslookup www.clouddeployment168.site`

**預期結果：**

```
Frame 1: DNS Query (你的電腦 -> 8.8.8.8)
Frame 2: DNS Response (8.8.8.8 -> 你的電腦)
```

**分析：**
- 查詢成功
- 只有一次查詢和一次回應
- 沒有重傳

---

### 場景 2：DNS 被封鎖

**步驟：**

1. 封鎖第一個 DNS（例如：8.8.8.8）
   ```bash
   sudo pfctl -a custom -f - <<< 'block drop out quick proto udp from any to 8.8.8.8 port 53'
   ```

2. 開啟 Wireshark，過濾器：`dns || icmp`

3. 執行：`nslookup www.clouddeployment168.site`

**預期結果：**

```
Frame 1: DNS Query (你的電腦 -> 8.8.8.8)
Frame 2: ICMP Destination Unreachable (8.8.8.8 -> 你的電腦)
Frame 3: DNS Query Retransmission (你的電腦 -> 8.8.8.8)
Frame 4: DNS Query (你的電腦 -> 其他 DNS 伺服器)
Frame 5: DNS Response (其他 DNS 伺服器 -> 你的電腦)
```

**分析：**
- 第一個 DNS 查詢失敗（被封鎖）
- 系統重傳查詢
- 系統自動切換到第二個 DNS
- 第二個 DNS 成功回應

---

### 場景 3：DNS 延遲

**步驟：**

1. 限制第一個 DNS 的頻寬（模擬延遲）
2. 開啟 Wireshark
3. 執行查詢

**預期結果：**

```
Frame 1: DNS Query (你的電腦 -> DNS1)
Frame 2: DNS Query (你的電腦 -> DNS2)  # 系統等不及，切換到第二個
Frame 3: DNS Response (DNS2 -> 你的電腦)
Frame 4: DNS Response (DNS1 -> 你的電腦)  # 延遲的回應（已不需要）
```

**分析：**
- 系統在等待第一個 DNS 回應時，切換到第二個
- 兩個 DNS 都回應了，但系統使用第一個收到的

---

## 📈 分析技巧

### 1. 查看時間軸

在 Wireshark 中，查看「Time」欄位：

- **正常查詢**：< 100ms
- **重傳間隔**：通常 1-3 秒
- **切換時間**：系統等待逾時後切換（通常 3-5 秒）

### 2. 查看封包詳情

點擊封包，查看詳細資訊：

- **DNS 查詢**：查看 `dns.qry.name`、`dns.qry.type`
- **DNS 回應**：查看 `dns.resp.name`、`dns.a`（IP 位址）
- **錯誤碼**：查看 `dns.flags.rcode`（0 = 成功）

### 3. 統計分析

**查看 DNS 統計：**

1. 選單：`Statistics` → `Protocol Hierarchy`
2. 展開 `DNS`，查看：
   - 查詢數量
   - 回應數量
   - 錯誤數量

**查看對話統計：**

1. 選單：`Statistics` → `Conversations`
2. 選擇 `IPv4` 或 `UDP`
3. 查看 DNS 伺服器的對話統計

---

## 💡 實用技巧

### 1. 儲存過濾器

將常用的過濾器儲存：

1. 輸入過濾器
2. 點擊過濾器欄位右側的「+」
3. 輸入名稱並儲存

### 2. 標記重要封包

1. 右鍵點擊封包
2. 選擇 `Mark/Unmark Packet`
3. 使用過濾器：`frame.marked == 1` 只顯示標記的封包

### 3. 匯出封包

1. 選擇要匯出的封包
2. `File` → `Export Specified Packets`
3. 選擇格式（通常使用 `.pcap`）

### 4. 追蹤 DNS 流程

1. 右鍵點擊 DNS 查詢封包
2. 選擇 `Follow` → `UDP Stream`
3. 查看完整的 DNS 對話流程

---

## 🐛 常見問題

### Q: 看不到 DNS 封包？

**A:** 
1. 確認選擇了正確的網路介面
2. 確認過濾器設定正確：`dns`
3. 確認有執行 DNS 查詢

### Q: 看到太多封包？

**A:** 
1. 使用更精確的過濾器：`dns.qry.name == "your-domain.com"`
2. 只捕獲特定時間範圍的封包

### Q: 如何知道系統切換了 DNS？

**A:** 
1. 查看查詢的目標 IP（`ip.dst`）
2. 如果看到多個不同的 DNS 伺服器 IP，表示系統在切換
3. 查看重傳封包（`dns.flags.retransmission == 1`）

---

## 📚 相關資源

- [Wireshark 官方文件](https://www.wireshark.org/docs/)
- [DNS 封包格式](https://en.wikipedia.org/wiki/Domain_Name_System#DNS_message_format)
- [Wireshark 過濾器語法](https://www.wireshark.org/docs/wsug_html_chunked/ChWorkWithDisplayFilters.html)

---

## ✅ 檢查清單

使用 Wireshark 分析前，確認：

- [ ] Wireshark 已安裝
- [ ] 選擇了正確的網路介面
- [ ] 設定了適當的過濾器
- [ ] 準備執行 DNS 查詢
- [ ] 知道要觀察什麼（查詢、回應、重傳、切換）

---

## 🎉 完成！

現在你可以使用 Wireshark 深入分析 DNS 故障切換行為了！

如有問題，請參考故障排除章節或 Wireshark 官方文件。
