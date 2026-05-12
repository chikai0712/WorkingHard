# DNS 查詢監控腳本 v1.0 使用文檔

## 📋 概述

`dns-query-monitor.sh` 是一個強大的 DNS 監控工具，支援兩種監控模式：
- **直接查詢模式**：快速測試各個 NS 的可用性
- **追蹤模式**：觀察完整的 DNS 解析路徑和故障切換

## ✅ 測試結果

所有功能測試通過：
- ✅ 語法檢查正確
- ✅ 幫助功能正常
- ✅ 所有必要命令已安裝（dig, bc, date）
- ✅ 所有核心函數存在
- ✅ AWS 和 Google NS 配置完整

## 🚀 快速開始

### 基本用法

```bash
# 直接查詢模式（每秒監控一次）
bash dns-query-monitor.sh 1 www.clouddeployment168.site

# 追蹤模式（每 5 秒追蹤一次）
bash dns-query-monitor.sh --trace 5 www.clouddeployment168.site

# 查看幫助
bash dns-query-monitor.sh --help
```

## 📖 詳細說明

### 模式 1：直接查詢模式（預設）

**特點：**
- ⚡ 快速：每個 NS 2 秒超時
- 📊 清晰：顯示所有 8 個 NS 的狀態
- 🎯 精準：立即定位故障的 NS
- 💰 輕量：適合高頻監控

**使用場景：**
- 日常健康監控
- 快速故障定位
- 高頻率監控（每 1-5 秒）

**輸出示例：**
```
[2025-02-07 10:30:15] 第 1 輪監控
AWS Route53 NS:
✓ AWS-NS-1 (205.251.197.44) - 45ms → 35.74.79.10
✓ AWS-NS-2 (205.251.199.48) - 52ms → 35.74.79.10
✓ AWS-NS-3 (205.251.192.236) - 48ms → 35.74.79.10
✓ AWS-NS-4 (205.251.195.65) - 50ms → 35.74.79.10

Google Cloud DNS NS:
✓ Google-NS-1 (216.239.32.108) - 38ms → 35.74.79.10
✓ Google-NS-2 (216.239.34.108) - 42ms → 35.74.79.10
✓ Google-NS-3 (216.239.36.108) - 40ms → 35.74.79.10
✓ Google-NS-4 (216.239.38.108) - 45ms → 35.74.79.10

統計:
  AWS NS: 4/4 可查詢
  Google NS: 4/4 可查詢
```

### 模式 2：追蹤模式（`--trace`）

**特點：**
- 🔍 完整：顯示從根 DNS 到最終 IP 的完整路徑
- 🔄 可視：觀察故障切換過程
- 📈 真實：模擬實際遞迴解析器行為
- 🎓 教育：理解 DNS 工作原理

**使用場景：**
- 驗證故障切換機制
- 診斷 DNS 解析問題
- 觀察防火牆阻擋效果
- 低頻率深度監控（每 5-30 秒）

**輸出示例：**
```
[2025-02-07 10:35:20] 第 1 輪追蹤監控

執行 dig +trace 遞迴追蹤...
⚠ 追蹤成功但有 4 次超時 - 8523ms → 35.74.79.10
   最終使用 NS: 216.239.32.108
   追蹤路徑:
     .                       518400  IN      NS      a.root-servers.net.
     .                       518400  IN      NS      b.root-servers.net.
     site.                   172800  IN      NS      a0.nic.site.
     clouddeployment168.site. 3600   IN      NS      ns-cloud-c1.googledomains.com.
     www.clouddeployment168.site. 300 IN     A       35.74.79.10

✓ 本輪追蹤成功
```

## 🎯 實戰場景

### 場景 1：日常監控

```bash
# 每秒監控，快速發現問題
bash dns-query-monitor.sh 1 www.clouddeployment168.site
```

### 場景 2：故障切換測試

```bash
# 終端 1：啟動追蹤監控
bash dns-query-monitor.sh --trace 10 www.clouddeployment168.site

# 終端 2：執行防火牆阻擋測試
sudo bash ../../Website/dns-failover-test.sh
```

### 場景 3：雙模式並行監控

```bash
# 終端 1：直接查詢（看各 NS 狀態）
bash dns-query-monitor.sh 2 www.clouddeployment168.site

# 終端 2：追蹤模式（看故障切換）
bash dns-query-monitor.sh --trace 10 www.clouddeployment168.site
```

### 場景 4：長時間監控

```bash
# 後台運行，記錄到日誌
nohup bash dns-query-monitor.sh 5 www.clouddeployment168.site > monitor.log 2>&1 &

# 查看日誌
tail -f monitor.log

# 停止監控
pkill -f dns-query-monitor.sh
```

## 📊 日誌分析

### 日誌位置

```bash
/tmp/dns_query_monitor_YYYYMMDD_HHMMSS.log
```

### 日誌格式

**直接查詢模式：**
```
[2025-02-07 10:30:15] SUCCESS | AWS-NS-1 | 205.251.197.44 | 45ms | 35.74.79.10
[2025-02-07 10:30:15] TIMEOUT | AWS-NS-2 | 205.251.199.48 | >2s | -
[2025-02-07 10:30:15] SUMMARY | AWS: 3/4 | Google: 4/4
```

**追蹤模式：**
```
[2025-02-07 10:35:20] TRACE_SUCCESS | 8523ms | 35.74.79.10 | NS: 216.239.32.108 | Timeouts: 4
[完整的 dig +trace 輸出]
---
```

### 分析命令

```bash
# 統計成功率
grep "SUMMARY" /tmp/dns_query_monitor_*.log | tail -20

# 查看失敗記錄
grep "TIMEOUT\|FAILED" /tmp/dns_query_monitor_*.log

# 統計平均響應時間
grep "SUCCESS" /tmp/dns_query_monitor_*.log | awk -F'|' '{print $4}' | sed 's/ms//' | awk '{sum+=$1; count++} END {print "平均:", sum/count, "ms"}'

# 查看追蹤中的超時次數
grep "Timeouts:" /tmp/dns_query_monitor_*.log
```

## 🔧 故障排除

### 問題 1：dig 權限錯誤

**錯誤訊息：**
```
bind: Operation not permitted
dig: isc_socket_bind: unexpected error
```

**解決方案：**
```bash
# 方案 1：使用 sudo
sudo bash dns-query-monitor.sh 1 www.clouddeployment168.site

# 方案 2：使用 nslookup（腳本會自動降級）
# 腳本已內建 nslookup 備用方案
```

### 問題 2：無法解析域名

**檢查步驟：**
```bash
# 1. 測試網路連線
ping -c 3 8.8.8.8

# 2. 測試 DNS 查詢
nslookup www.clouddeployment168.site 8.8.8.8

# 3. 檢查防火牆規則
sudo pfctl -sr | grep "port 53"

# 4. 清除 DNS 快取
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

### 問題 3：追蹤模式一直超時

**可能原因：**
- 防火牆阻擋了 DNS 查詢
- 網路連線不穩定
- DNS 服務器故障

**檢查方法：**
```bash
# 手動執行 dig +trace
dig +trace www.clouddeployment168.site

# 檢查是否有防火牆規則
sudo pfctl -sr | grep "53"

# 測試直接查詢
dig @8.8.8.8 www.clouddeployment168.site
```

## 📈 性能建議

### 監控間隔建議

| 場景 | 直接查詢模式 | 追蹤模式 |
|------|-------------|---------|
| 生產環境監控 | 5-10 秒 | 30-60 秒 |
| 故障測試 | 1-2 秒 | 5-10 秒 |
| 長期監控 | 30-60 秒 | 不推薦 |

### 資源消耗

| 模式 | CPU | 網路 | 適合頻率 |
|------|-----|------|---------|
| 直接查詢 | 低 | 低 | 每秒 |
| 追蹤模式 | 中 | 高 | 每 5-30 秒 |

## 🎓 dig +trace 深入理解

### 解析流程

```
1. 查詢根 DNS (.)
   └─> 返回 .site TLD 的 NS

2. 查詢 .site TLD NS
   └─> 返回 clouddeployment168.site 的 NS (AWS + Google)

3. 查詢 clouddeployment168.site NS
   ├─> 嘗試 AWS NS (如果被阻擋會超時)
   └─> 切換到 Google NS (成功)

4. 最終獲得 A 記錄
   └─> www.clouddeployment168.site → 35.74.79.10
```

### 故障切換觀察

當 AWS NS 被阻擋時，`dig +trace` 會顯示：
```
;; connection timed out; no servers could be reached
;; Received 512 bytes from 216.239.32.108#53(ns-cloud-c1.googledomains.com) in 45 ms
```

這清楚顯示了系統從失敗的 NS 切換到成功的 NS！

## 🔗 相關腳本

- `dns-failover-test.sh` - DNS 故障切換測試
- `block-dns.sh` - DNS 阻擋工具
- `dns_test_pro.sh` - 專業 DNS 測試工具
- `test-monitor.sh` - 監控腳本測試工具

## 📝 版本歷史

### v1.0 (2025-02-07)
- ✅ 初始版本
- ✅ 支援直接查詢模式
- ✅ 支援 dig +trace 追蹤模式
- ✅ 雙模式切換
- ✅ 完整日誌記錄
- ✅ 統計功能
- ✅ 故障切換可視化

## 💡 最佳實踐

1. **日常監控**：使用直接查詢模式，間隔 5-10 秒
2. **故障測試**：使用追蹤模式，配合防火牆測試
3. **組合使用**：開兩個終端，同時運行兩種模式
4. **日誌分析**：定期檢查日誌，分析趨勢
5. **告警設置**：可以結合 grep 和郵件通知實現告警

## 🎯 總結

### 何時使用直接查詢模式？
- ✅ 需要快速監控各個 NS 的健康狀態
- ✅ 需要高頻率監控（每 1-5 秒）
- ✅ 需要精準定位故障的 NS
- ✅ 資源有限的環境

### 何時使用追蹤模式？
- ✅ 需要驗證故障切換機制
- ✅ 需要診斷 DNS 解析問題
- ✅ 需要觀察完整的解析路徑
- ✅ 需要教學或演示 DNS 工作原理

---

**作者**: CK  
**版本**: v1.0  
**日期**: 2025-02-07  
**授權**: MIT

