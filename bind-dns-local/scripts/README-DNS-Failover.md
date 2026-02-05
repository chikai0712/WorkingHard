# DNS Failover 測試腳本說明

本腳本整合了 `Website/dig-trace-failover.sh` 的成功方法，用於測試 AWS/Google NS 異常時的 DNS failover 行為。

## 核心方法（參考 dig-trace-failover.sh）

### 1. 使用 `dig +trace` 繞過系統 DNS

**關鍵概念**：你無法控制 8.8.8.8 與 AWS 之間的網路。若只在本地封鎖 AWS NS，然後問 8.8.8.8，8.8.8.8 仍可連上 AWS，回傳給你的結果仍是正常的。

**解決方案**：讓「你的電腦」扮演遞回解析器 → 使用 `dig +trace`。

加上 `+trace` 時，dig 會繞過系統 DNS，由本機從根 (.) 一層層往下問，此時防火牆規則會生效（發出請求的是你的電腦）。

### 2. 使用 `pfctl -f` 直接載入規則

參考 `dig-trace-failover.sh` 的成功方法：
- 使用 `pfctl -f` 直接載入規則文件，而不是合併到 `/etc/pf.conf`
- 使用 `pfctl -F all` 來重置防火牆（而不是 `pfctl -f /etc/pf.conf`）

### 3. 使用 `time` 命令測量實際耗時

使用 `time` 命令來測量 `dig +trace` 和 `nslookup` 的實際耗時，更能反映真實的 failover 時間。

## 測試流程

1. **基準測試**：無阻擋，確認域名可正常解析
2. **阻擋 AWS NS**：使用 `dig +trace` 測試，應從 Google NS 解析到 Google EC2
3. **阻擋 Google NS**：使用 `dig +trace` 測試，應從 AWS NS 解析到 AWS EC2
4. **nslookup 測試**：測試真實使用者等待時間

## 使用方法

```bash
cd bind-dns-local/scripts
sudo bash ./dns-failover-test.sh [域名] [AWS_EC2_IP] [Google_EC2_IP]

# 範例
sudo bash ./dns-failover-test.sh www.example.com 3.3.3.3 2.2.2.2
```

## 與 dig-trace-failover.sh 的差異

- **整合性**：整合了 HTTP 連線測試，驗證實際網站內容
- **EC2 部署**：包含完整的 EC2 部署指南
- **簡化流程**：保留核心測試方法，簡化部分流程

## 日誌位置

- 主日誌: `/tmp/dns_failover_test_YYYYMMDD_HHMMSS.log`
- Debug: `/tmp/dns_failover_debug.log`
- 錯誤: `/tmp/dns_failover_errors.log`

## 注意事項

- ⚠️ 需要 `sudo` 權限（用於修改防火牆規則）
- ⚠️ 僅支援 macOS（使用 PF 防火牆）
- ⚠️ 測試完成後會自動還原防火牆規則（使用 `pfctl -F all`）
