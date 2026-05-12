# DNS 雙權威主機故障切換驗證方法

## 📋 概述

本文檔提供三種驗證「雙權威主機（Multi-Vendor）在單方故障時的表現」的方法。這些方法可以安全地模擬 DNS 故障場景，無需等待真實的 AWS 或其他 DNS 提供商當機。

---

## 🎯 驗證目標

1. **測量故障切換時間**：當一個 DNS 提供商故障時，切換到備用提供商的時間
2. **驗證架構正確性**：確保雙 DNS 配置能夠真正提供高可用性
3. **評估用戶體驗影響**：了解故障時玩家會感受到的延遲

---

## ⚠️ 重要前提

在執行任何驗證方法之前，**必須先確認架構配置正確**（見方法三）。錯誤的配置會導致「假的高可用性」，即使測試通過也無法在真實故障時提供保護。

---

## 方法一：本機防火牆模擬（最推薦）

### 📌 適用場景

- ✅ 快速驗證基本故障切換行為
- ✅ 測量本地 DNS 查詢的實際延遲
- ✅ 開發和測試環境驗證
- ✅ 模擬玩家真實體驗

### 🔧 實施步驟

#### 步驟 1：找出 AWS Name Server IP

```bash
# 查詢你的域名在 AWS Route 53 分配到的 Name Server
dig NS your-domain.com

# 假設其中一台是 ns-111.awsdns-11.com
# 找出它的 IP 地址
ping ns-111.awsdns-11.com
# 或
dig +short ns-111.awsdns-11.com

# 記下這個 IP，例如 205.251.192.11
```

#### 步驟 2：設防火牆「封鎖」這個 IP（模擬斷線）

**Windows (PowerShell 系統管理員):**

```powershell
# 封鎖 AWS DNS IP
New-NetFirewallRule -DisplayName "Block AWS DNS" `
    -Direction Outbound `
    -RemoteAddress 205.251.192.11 `
    -Action Block

# 驗證規則已建立
Get-NetFirewallRule -DisplayName "Block AWS DNS"
```

**macOS:**

```bash
# 使用 pfctl 封鎖（需要 root 權限）
sudo pfctl -f - <<EOF
block out quick on en0 to 205.251.192.11
EOF

# 啟用防火牆
sudo pfctl -e
```

**Linux (iptables):**

```bash
# 封鎖 AWS DNS IP
sudo iptables -A OUTPUT -d 205.251.192.11 -j DROP

# 查看規則
sudo iptables -L OUTPUT -n
```

#### 步驟 3：清除本機 DNS Cache

為了確保電腦真的重新去查詢，而不是讀舊紀錄。

**Windows:**
```cmd
ipconfig /flushdns
```

**macOS:**
```bash
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

**Linux:**
```bash
# 根據使用的 DNS 服務而定
sudo systemd-resolve --flush-caches  # systemd-resolved
# 或
sudo service nscd restart  # nscd
```

#### 步驟 4：進行測試與計時

**Linux/macOS:**
```bash
# 測量查詢時間
time nslookup your-game.com
# 或
time dig your-game.com
```

**Windows (PowerShell):**
```powershell
# 測量查詢時間
Measure-Command { nslookup your-game.com }
```

**使用 dig 詳細觀察:**
```bash
dig your-game.com +stats
# 觀察 Query time 欄位
```

#### 步驟 5：清理（重要！）

**Windows:**
```powershell
Remove-NetFirewallRule -DisplayName "Block AWS DNS"
```

**macOS:**
```bash
sudo pfctl -d  # 停用防火牆
# 或編輯 /etc/pf.conf 移除規則
```

**Linux:**
```bash
sudo iptables -D OUTPUT -d 205.251.192.11 -j DROP
```

### 👀 預期結果

- **正常情況**：查詢時間 < 100ms
- **模擬故障**：查詢時間約 2-4 秒（這是 OS 在等 AWS 回應）
- **成功切換**：最後顯示出正確的 IP（因為切換到 Google 了）

### ⚠️ 注意事項

1. **記得恢復防火牆規則**，否則以後查 AWS 都會慢
2. 此方法僅測試本機行為，不測試 ISP 遞迴解析器
3. 需要管理員/root 權限

---

## 方法二：建立「爛掉的子網域」（驗證 ISP Resolver 行為）

### 📌 適用場景

- ✅ 測試真實網路環境（不同 ISP）
- ✅ 驗證遞迴解析器的重試機制
- ✅ 測試全球不同地區的行為
- ✅ 模擬真實故障場景

### 🔧 實施步驟

#### 步驟 1：建立測試子網域

在你的 AWS 和 Google DNS 設定中，新增一個子網域：
- `failover-test.yourdomain.com`

#### 步驟 2：設定 NS 記錄（故意設錯）

**在 AWS Route 53:**
```
failover-test.yourdomain.com  NS  ns-bad.192.0.2.1
failover-test.yourdomain.com  NS  ns-cloud-c1.googledomains.com
```

**在 Google Cloud DNS:**
```
failover-test.yourdomain.com  NS  ns-bad.192.0.2.1
failover-test.yourdomain.com  NS  ns-cloud-c1.googledomains.com
```

**說明：**
- `192.0.2.1` 是 RFC 3330 保留地址，通常不會有回應，能完美模擬 Timeout
- 第一個 NS 指向壞的 IP（模擬 AWS 壞掉）
- 第二個 NS 指向 Google 正常的 Name Server

#### 步驟 3：使用不同網路查詢

**使用 dig 觀察回應時間:**
```bash
dig failover-test.yourdomain.com

# 觀察重點：
# - Query time: 欄位（應該會顯示 2000-4000 msec）
# - 是否成功解析（應該會成功，因為切換到 Google）
```

**使用不同遞迴解析器測試:**
```bash
# Google DNS
dig @8.8.8.8 failover-test.yourdomain.com

# Cloudflare DNS
dig @1.1.1.1 failover-test.yourdomain.com

# 本地 ISP DNS
dig failover-test.yourdomain.com
```

**使用線上工具:**
- https://www.whatsmydns.net/
- https://dnschecker.org/
- https://mxtoolbox.com/DNSLookup.aspx

#### 步驟 4：觀察與記錄

**正常情況：**
```
;; Query time: 50 msec
;; SERVER: 8.8.8.8#53(8.8.8.8)
```

**故障切換情況：**
```
;; Query time: 2000 msec  ← 先踩到了地雷（壞 IP），超時後才去問 Google
;; SERVER: 8.8.8.8#53(8.8.8.8)
```

**失敗情況（較少見）:**
```
;; status: SERVFAIL
```
這代表該 ISP 的設定不支援這種自動重試（可能發生在嚴格的 DNSSEC 設定下）

### ⚠️ 注意事項

1. **DNSSEC 驗證可能失敗**：如果啟用了 DNSSEC，錯誤的 NS 記錄可能導致 SERVFAIL
2. **可能被搜索引擎索引**：建議使用 robots.txt 或 noindex
3. **需要維護**：測試完成後記得清理或保留用於長期監控

### 🔍 進階測試

**測試不同查詢類型:**
```bash
# A 記錄
dig failover-test.yourdomain.com A

# AAAA 記錄
dig failover-test.yourdomain.com AAAA

# MX 記錄
dig failover-test.yourdomain.com MX
```

**使用 tcpdump 抓包觀察:**
```bash
sudo tcpdump -i any -n port 53
# 在另一個終端執行 dig
# 觀察 DNS 查詢的完整流程
```

---

## 方法三：圖解確認架構風險（架構驗證）

### 📌 適用場景

- ✅ 架構設計階段驗證
- ✅ 配置變更後的檢查
- ✅ 故障前的預防性檢查
- ✅ 其他方法的前提條件

### 🔧 驗證清單

#### ✅ 檢查 1：Registrar 層級設定（最重要！）

**去你的網域註冊商（GoDaddy/Namecheap 等）檢查：**

1. 登入域名註冊商管理介面
2. 找到「Nameservers」或「DNS 設定」欄位
3. 確認裡面**混合了 AWS 和 Google 的網址**

**✅ 正確範例：**
```
ns-11.awsdns-11.com
ns-cloud-c1.googledomains.com
ns-22.awsdns-22.com
ns-cloud-c2.googledomains.com
```

**❌ 錯誤範例：**
```
ns-11.awsdns-11.com
ns-22.awsdns-22.com
ns-33.awsdns-33.com
ns-44.awsdns-44.com
```
（只填了 AWS，然後在 AWS 裡面用 NS 記錄指去 Google - 這樣 AWS 掛了，沒人知道要去問 Google）

#### ✅ 檢查 2：Glue Records（如需要）

**什麼時候需要 Glue Records？**

- 當 NS 記錄指向的域名**與當前域名相同**時需要 Glue Records
- 例如：`example.com` 的 NS 記錄指向 `ns1.example.com`

**如何檢查：**

```bash
# 查詢根域名的 NS 記錄
dig NS yourdomain.com

# 查詢每個 NS 的 IP（Glue Records）
dig +additional yourdomain.com NS
```

**範例：**
```
;; ANSWER SECTION:
yourdomain.com.    3600    IN    NS    ns1.yourdomain.com.
yourdomain.com.    3600    IN    NS    ns2.yourdomain.com.

;; ADDITIONAL SECTION:
ns1.yourdomain.com. 3600   IN    A     192.0.2.1
ns2.yourdomain.com. 3600   IN    A     192.0.2.2
```

#### ✅ 檢查 3：NS 記錄一致性

**在所有權威 DNS 中查詢 NS 記錄：**

```bash
# 從 AWS Name Server 查詢
dig @ns-11.awsdns-11.com yourdomain.com NS

# 從 Google Name Server 查詢
dig @ns-cloud-c1.googledomains.com yourdomain.com NS
```

**確認要點：**
- ✅ 所有權威 DNS 返回的 NS 記錄**列表必須相同**
- ✅ 順序可以不同，但內容必須一致
- ✅ 數量必須相同

**✅ 正確範例：**
```
# AWS 返回
yourdomain.com. NS ns-11.awsdns-11.com
yourdomain.com. NS ns-cloud-c1.googledomains.com
yourdomain.com. NS ns-22.awsdns-22.com
yourdomain.com. NS ns-cloud-c2.googledomains.com

# Google 返回（順序不同，但內容相同）
yourdomain.com. NS ns-cloud-c1.googledomains.com
yourdomain.com. NS ns-11.awsdns-11.com
yourdomain.com. NS ns-cloud-c2.googledomains.com
yourdomain.com. NS ns-22.awsdns-22.com
```

#### ✅ 檢查 4：DNS 記錄同步

**檢查 A 記錄是否在所有 Name Server 中一致：**

```bash
# 從不同 Name Server 查詢 A 記錄
dig @ns-11.awsdns-11.com yourdomain.com A
dig @ns-cloud-c1.googledomains.com yourdomain.com A
```

**確認要點：**
- ✅ 所有 Name Server 返回的 IP 必須相同
- ✅ TTL 可以不同（但建議保持一致）

### 📊 驗證腳本

創建一個自動化驗證腳本：

```bash
#!/bin/bash
# verify-dns-config.sh

DOMAIN="yourdomain.com"
AWS_NS="ns-11.awsdns-11.com"
GOOGLE_NS="ns-cloud-c1.googledomains.com"

echo "🔍 驗證 DNS 架構配置..."
echo ""

# 檢查 Registrar 層級
echo "1. 檢查 Registrar 層級 NS 記錄..."
REGISTRAR_NS=$(dig +short NS $DOMAIN)
echo "   Registrar 返回的 NS:"
echo "$REGISTRAR_NS" | while read ns; do
    echo "   - $ns"
done
echo ""

# 檢查 NS 記錄一致性
echo "2. 檢查 NS 記錄一致性..."
AWS_NS_LIST=$(dig @$AWS_NS +short NS $DOMAIN | sort)
GOOGLE_NS_LIST=$(dig @$GOOGLE_NS +short NS $DOMAIN | sort)

if [ "$AWS_NS_LIST" = "$GOOGLE_NS_LIST" ]; then
    echo "   ✅ NS 記錄一致"
else
    echo "   ❌ NS 記錄不一致！"
    echo "   AWS 返回:"
    echo "$AWS_NS_LIST"
    echo "   Google 返回:"
    echo "$GOOGLE_NS_LIST"
fi
echo ""

# 檢查 A 記錄一致性
echo "3. 檢查 A 記錄一致性..."
AWS_A=$(dig @$AWS_NS +short A $DOMAIN | sort)
GOOGLE_A=$(dig @$GOOGLE_NS +short A $DOMAIN | sort)

if [ "$AWS_A" = "$GOOGLE_A" ]; then
    echo "   ✅ A 記錄一致"
else
    echo "   ❌ A 記錄不一致！"
    echo "   AWS 返回: $AWS_A"
    echo "   Google 返回: $GOOGLE_A"
fi
```

### ⚠️ 常見錯誤

1. **只在 AWS 設定 NS 記錄指向 Google**
   - ❌ 錯誤：在 AWS Route 53 中設定 NS 記錄指向 Google
   - ✅ 正確：在 Registrar 層級設定混合 NS

2. **NS 記錄不一致**
   - ❌ 錯誤：AWS 返回 4 個 NS，Google 返回 2 個 NS
   - ✅ 正確：所有權威 DNS 返回相同的 NS 列表

3. **缺少 Glue Records**
   - ❌ 錯誤：NS 指向同域名的子域名但沒有 Glue Records
   - ✅ 正確：在 Registrar 設定 Glue Records

---

## 📊 方法比較

| 方法 | 優點 | 缺點 | 適用場景 |
|------|------|------|---------|
| **方法一** | 快速、安全、真實模擬 | 僅測試本機 | 快速驗證、開發測試 |
| **方法二** | 真實網路環境、ISP 行為 | 配置複雜、可能失敗 | 生產環境驗證 |
| **方法三** | 預防性、一次性 | 不測試實際故障 | 架構設計、配置檢查 |

---

## 🎯 推薦執行順序

1. **先執行方法三**（架構驗證）
   - 確保基礎配置正確
   - 避免在錯誤架構上測試

2. **再執行方法一**（本機模擬）
   - 快速驗證基本行為
   - 測量本地延遲

3. **最後執行方法二**（子網域測試）
   - 驗證真實網路環境
   - 測試不同 ISP 行為

---

## 📝 測試記錄模板

### 測試記錄

**測試日期：** 2025-XX-XX  
**測試人員：** XXX  
**測試域名：** yourdomain.com  

#### 方法一：本機防火牆模擬

| 項目 | 結果 |
|------|------|
| AWS NS IP | 205.251.192.11 |
| 正常查詢時間 | XX ms |
| 模擬故障查詢時間 | XXXX ms |
| 切換是否成功 | ✅/❌ |
| 備註 | |

#### 方法二：子網域測試

| 項目 | 結果 |
|------|------|
| 測試子網域 | failover-test.yourdomain.com |
| Google DNS 查詢時間 | XX ms |
| Cloudflare DNS 查詢時間 | XX ms |
| ISP DNS 查詢時間 | XX ms |
| 是否出現 SERVFAIL | ✅/❌ |
| 備註 | |

#### 方法三：架構驗證

| 項目 | 結果 |
|------|------|
| Registrar NS 設定 | ✅/❌ |
| NS 記錄一致性 | ✅/❌ |
| A 記錄一致性 | ✅/❌ |
| Glue Records | ✅/❌/不需要 |
| 備註 | |

---

## 🔗 相關資源

- [RFC 1034 - Domain Names - Concepts and Facilities](https://tools.ietf.org/html/rfc1034)
- [RFC 1035 - Domain Names - Implementation and Specification](https://tools.ietf.org/html/rfc1035)
- [RFC 3330 - Special-Use IPv4 Addresses](https://tools.ietf.org/html/rfc3330)
- [DNS 故障恢復時間驗證方案](../Host%20DNS/DNS故障恢復時間驗證方案.md)

---

**最後更新：** 2025-12-29  
**文件版本：** v1.0

