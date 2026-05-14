# DNS 檢測工具網站清單

本文件列出常用的 DNS 檢測與診斷工具網站，用於驗證 DNS 解析、傳播狀態、記錄配置等。

## 🌐 全球 DNS 傳播檢測

### 1. DNS Checker
- **網址**：https://dnschecker.org
- **功能**：
  - 全球多個地點的 DNS 解析檢測
  - 檢查 A、AAAA、CNAME、MX、TXT、NS 記錄
  - DNS 傳播狀態視覺化
  - 歷史記錄查詢
- **適用場景**：驗證 DNS 變更是否已全球傳播

### 2. What's My DNS
- **網址**：https://www.whatsmydns.net
- **功能**：
  - 全球 DNS 查詢測試
  - 多種記錄類型檢測（A、AAAA、MX、NS、TXT、CNAME）
  - 地圖視覺化顯示解析結果
- **適用場景**：快速檢查全球 DNS 解析狀態

### 3. DNSPerf
- **網址**：https://www.dnsperf.com
- **功能**：
  - DNS 解析速度測試
  - 全球 DNS 伺服器效能比較
  - 權威 DNS 伺服器效能排名
- **適用場景**：評估 DNS 提供商效能

## 🔍 DNS 記錄查詢工具

### 4. MXToolbox
- **網址**：https://mxtoolbox.com
- **功能**：
  - DNS 記錄查詢（A、MX、TXT、SPF、DMARC、DKIM）
  - 黑名單檢查
  - 郵件伺服器診斷
  - 網站監控
- **適用場景**：郵件相關 DNS 記錄診斷、SPF/DMARC 驗證

### 5. DNSstuff
- **網址**：https://www.dnsstuff.com
- **功能**：
  - 完整的 DNS 記錄查詢
  - WHOIS 查詢
  - 反向 DNS 查詢
  - 網路工具集
- **適用場景**：全面的 DNS 診斷

### 6. IntoDNS
- **網址**：https://intodns.com
- **功能**：
  - DNS 健康檢查
  - 記錄配置錯誤檢測
  - 郵件伺服器配置檢查
  - 詳細的診斷報告
- **適用場景**：DNS 配置完整性檢查

## 🔐 安全性檢測

### 7. SecurityTrails
- **網址**：https://securitytrails.com
- **功能**：
  - DNS 歷史記錄查詢
  - 子域名枚舉
  - IP 歷史記錄
  - 安全威脅情報
- **適用場景**：安全審計、DNS 歷史變更追蹤

### 8. DNS History
- **網址**：https://dnshistory.org
- **功能**：
  - DNS 記錄歷史查詢
  - 變更追蹤
- **適用場景**：調查 DNS 記錄變更歷史

## 📊 WHOIS 與域名資訊

### 9. WHOIS.net
- **網址**：https://www.whois.net
- **功能**：
  - WHOIS 查詢
  - 域名註冊資訊
  - 到期日期查詢
- **適用場景**：域名所有權驗證、到期日檢查

### 10. ICANN Lookup
- **網址**：https://lookup.icann.org
- **功能**：
  - 官方 WHOIS 查詢
  - 註冊商資訊
  - 域名狀態查詢
- **適用場景**：官方域名資訊查詢

## 🛠️ 進階診斷工具

### 11. DNSlytics
- **網址**：https://dnslytics.com
- **功能**：
  - DNS 記錄查詢
  - 反向 IP 查詢
  - 域名分析
  - 威脅情報
- **適用場景**：進階 DNS 分析

### 12. ViewDNS.info
- **網址**：https://viewdns.info
- **功能**：
  - 多種 DNS 工具
  - IP 查詢
  - 反向 DNS 查詢
  - 端口掃描
- **適用場景**：綜合網路診斷

## 📱 命令列工具

### 本地工具（無需網站）

```bash
# dig - DNS 查詢工具
dig example.com
dig @8.8.8.8 example.com +short
dig +trace example.com

# nslookup - 基本 DNS 查詢
nslookup example.com
nslookup -type=MX example.com

# host - 簡單 DNS 查詢
host example.com
host -t MX example.com

# whois - WHOIS 查詢
whois example.com

# mtr - 網路路徑追蹤
mtr example.com
```

## 🎯 使用建議

### 日常監控
- **DNS Checker**：定期檢查 DNS 傳播狀態
- **MXToolbox**：監控郵件相關 DNS 記錄

### 故障排查
1. **DNS Checker** 或 **What's My DNS**：確認是否為全球性問題
2. **MXToolbox**：檢查特定記錄類型
3. **IntoDNS**：檢查配置錯誤
4. **命令列工具**：本地快速驗證

### 安全審計
- **SecurityTrails**：檢查 DNS 歷史變更
- **DNS History**：追蹤可疑變更

### 效能評估
- **DNSPerf**：比較不同 DNS 提供商效能

## 📝 注意事項

1. **快取影響**：某些工具可能使用快取的 DNS 結果，建議使用多個工具交叉驗證
2. **隱私考量**：部分工具會記錄查詢歷史，敏感域名請謹慎使用
3. **API 限制**：付費工具通常有更高的查詢限制和更詳細的報告

---

**最後更新**：2025-01-XX  
**維護者**：DNS Team

