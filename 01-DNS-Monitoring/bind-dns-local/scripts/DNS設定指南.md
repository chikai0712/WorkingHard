# macOS DNS 設定指南 - 使用本機 Docker BIND

本指南說明如何將 macOS 的 DNS 設定指向本機的 Docker BIND DNS 服務器。

## 前置需求

1. ✅ BIND DNS 容器正在運行
   ```bash
   cd bind-dns-local
   ./scripts/start.sh
   ```

2. ✅ 確認 BIND 容器運行中
   ```bash
   docker ps | grep bind-dns-local
   ```

## 快速設定

### 方法 1：使用自動設定腳本（推薦）

```bash
cd bind-dns-local/scripts
sudo bash ./setup-macos-dns.sh
```

腳本會：
- ✅ 自動偵測主要網路介面
- ✅ 設定 DNS 為 127.0.0.1
- ✅ 清除 DNS 快取
- ✅ 測試 DNS 解析

### 方法 2：手動指定網路介面

```bash
# 列出所有網路介面
sudo bash ./setup-macos-dns.sh list

# 設定特定介面（例如 Wi-Fi）
sudo bash ./setup-macos-dns.sh set Wi-Fi

# 或設定乙太網路
sudo bash ./setup-macos-dns.sh set "USB 10/100/1000 LAN"
```

## 手動設定（不使用腳本）

### 步驟 1：找出網路介面名稱

```bash
networksetup -listallnetworkservices
```

常見的介面名稱：
- `Wi-Fi` - 無線網路
- `Ethernet` - 有線網路
- `USB 10/100/1000 LAN` - USB 網路卡

### 步驟 2：設定 DNS

```bash
# 設定 DNS 為本機 BIND
sudo networksetup -setdnsservers Wi-Fi 127.0.0.1

# 或設定多個 DNS（本機優先，然後備用）
sudo networksetup -setdnsservers Wi-Fi 127.0.0.1 8.8.8.8
```

### 步驟 3：清除 DNS 快取

```bash
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

### 步驟 4：驗證設定

```bash
# 查看當前 DNS 設定
networksetup -getdnsservers Wi-Fi

# 測試 DNS 解析
dig example.com
# 或
nslookup example.com
```

## 還原 DNS 設定

### 使用腳本還原

```bash
sudo bash ./setup-macos-dns.sh restore Wi-Fi
```

### 手動還原

```bash
# 還原為 DHCP 提供的 DNS
sudo networksetup -setdnsservers Wi-Fi "Empty"

# 清除快取
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

## 測試 DNS 解析

### 測試本機 BIND

```bash
# 直接查詢本機 BIND
dig @127.0.0.1 example.com

# 使用系統 DNS（應該會使用本機 BIND）
dig example.com
```

### 測試特定域名

```bash
# 測試腳本提供的測試功能
sudo bash ./setup-macos-dns.sh test example.com
```

## 常見問題

### 問題 1: DNS 設定後無法上網

**原因**：BIND 容器可能未正確配置或未運行

**解決方案**：
1. 檢查 BIND 容器狀態：`docker ps | grep bind-dns-local`
2. 查看 BIND 日誌：`docker logs bind-dns-local`
3. 還原 DNS 設定：`sudo bash ./setup-macos-dns.sh restore`

### 問題 2: 無法找到網路介面

**解決方案**：
```bash
# 列出所有介面
sudo bash ./setup-macos-dns.sh list

# 手動指定介面名稱
sudo bash ./setup-macos-dns.sh set "你的介面名稱"
```

### 問題 3: DNS 查詢很慢

**原因**：可能是 IPv6 查詢失敗導致延遲

**解決方案**：
1. 檢查 BIND 日誌中的 IPv6 錯誤（通常是正常的）
2. 確認 BIND 配置正確
3. 測試 IPv4 查詢：`dig +4 example.com`

### 問題 4: 設定後需要重新設定

**原因**：macOS 可能會在某些情況下重置網路設定

**解決方案**：
- 使用腳本快速重新設定
- 或將腳本加入快捷方式

## 進階設定

### 設定多個 DNS 伺服器（本機優先，備用公共 DNS）

```bash
sudo networksetup -setdnsservers Wi-Fi 127.0.0.1 8.8.8.8 1.1.1.1
```

這樣設定後：
- 優先使用本機 BIND (127.0.0.1)
- 如果本機 BIND 無法解析，使用 Google DNS (8.8.8.8)
- 最後使用 Cloudflare DNS (1.1.1.1)

### 僅對特定域名使用本機 BIND

macOS 不直接支援按域名選擇 DNS，但可以：
1. 使用本機 BIND 作為主要 DNS
2. 在 BIND 中配置轉發規則
3. 或使用 DNS 過濾工具

## 注意事項

1. ⚠️ **需要 sudo 權限**：修改系統 DNS 設定需要管理員權限
2. ⚠️ **備份設定**：建議在修改前記錄原始 DNS 設定
3. ⚠️ **測試連線**：設定後請測試網路連線是否正常
4. ⚠️ **容器狀態**：確保 BIND 容器持續運行，否則會影響 DNS 解析

## 快速參考

```bash
# 設定 DNS
sudo bash ./setup-macos-dns.sh set Wi-Fi

# 還原 DNS
sudo bash ./setup-macos-dns.sh restore Wi-Fi

# 查看當前設定
sudo bash ./setup-macos-dns.sh show Wi-Fi

# 列出所有介面
sudo bash ./setup-macos-dns.sh list

# 測試 DNS
sudo bash ./setup-macos-dns.sh test example.com
```
