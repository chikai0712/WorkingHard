# 多 NS DNS 異常檢測說明

## 📋 功能概述

本工具使用多個 ISP 的 Name Server (NS) 檢測域名解析是否異常，主要用於：

1. **DNS 劫持檢測**：檢測域名是否被解析到非預期的 IP 地址
2. **DNS 污染檢測**：檢測部分 NS 是否無法正常解析（可能被污染）
3. **解析一致性檢測**：比較不同 NS 的解析結果，發現異常差異

## 🎯 檢測原理

### 正常情況
```
域名: example.com
NS1 (8.8.8.8)    → 192.168.1.100 ✅
NS2 (1.1.1.1)    → 192.168.1.100 ✅
NS3 (9.9.9.9)    → 192.168.1.100 ✅
結果: 所有 NS 解析一致，都在白名單中 → OK
```

### DNS 劫持情況
```
域名: example.com
NS1 (8.8.8.8)    → 192.168.1.100 ✅ (在白名單中)
NS2 (1.1.1.1)    → 203.0.113.1   ❌ (不在白名單中)
NS3 (9.9.9.9)    → 192.168.1.100 ✅ (在白名單中)
結果: NS2 解析到異常 IP → CRITICAL
```

### DNS 污染情況
```
域名: example.com
NS1 (8.8.8.8)    → 192.168.1.100 ✅
NS2 (1.1.1.1)    → Timeout        ⚠️  (解析失敗)
NS3 (9.9.9.9)    → 192.168.1.100 ✅
結果: 部分 NS 解析失敗 → WARNING/CRITICAL
```

### 解析不一致情況
```
域名: example.com
NS1 (8.8.8.8)    → 192.168.1.100
NS2 (1.1.1.1)    → 192.168.1.101  (不同 IP)
NS3 (9.9.9.9)    → 192.168.1.100
結果: 不同 NS 解析到不同 IP → CRITICAL (可能被劫持)
```

## 🔍 異常檢測邏輯

### 異常判定條件

1. **IP 不在白名單中**
   - 任何 NS 解析出的 IP 不在白名單中
   - 可能原因：DNS 劫持、配置錯誤

2. **解析結果不一致**
   - 不同 NS 解析到不同的 IP 集合
   - 可能原因：DNS 劫持、緩存問題、配置錯誤

3. **部分 NS 解析失敗**
   - 部分 NS 成功，部分失敗
   - 可能原因：DNS 污染、網絡問題、NS 故障

### 檢測流程

```
1. 使用多個 NS 同時查詢域名
   ↓
2. 收集所有 NS 的解析結果
   ↓
3. 檢查每個 IP 是否在白名單中
   ↓
4. 比較不同 NS 的解析結果
   ↓
5. 分析異常情況
   ↓
6. 生成檢測報告
```

## 📊 使用範例

### 基本使用

```bash
# 使用默認的多個公共 DNS
python src/dns_checker_multi_ns.py -R example.com -W whitelist.txt
```

### 指定多個 NS

```bash
# 指定多個 ISP 的 NS
python src/dns_checker_multi_ns.py \
  -R example.com \
  -S 8.8.8.8,1.1.1.1,9.9.9.9,208.67.222.222 \
  -W whitelist.txt
```

### JSON 格式輸出

```bash
# 輸出 JSON 格式（便於自動化處理）
python src/dns_checker_multi_ns.py \
  -R example.com \
  -W whitelist.txt \
  --format json
```

### Nagios 格式輸出

```bash
# 輸出 Nagios 兼容格式
python src/dns_checker_multi_ns.py \
  -R example.com \
  -W whitelist.txt \
  --format nagios
```

## 📈 檢測報告範例

### 正常情況

```
================================================================================
DNS 檢測報告: example.com
================================================================================

📊 檢測摘要:
  總 NS 數量: 8
  成功: 8
  失敗: 0
  未知: 0
  解析一致性: ✅ 一致
  白名單驗證: ✅ 全部通過
  異常檢測: ✅ 正常

🔍 各 NS 檢測結果:
  ✅ 8.8.8.8:
    IP: 192.168.1.100
    白名單: ✅
    狀態: OK
    訊息: OK - example.com resolved to 192.168.1.100 (nameserver: 8.8.8.8)
  ...
```

### 異常情況

```
================================================================================
DNS 檢測報告: example.com
================================================================================

📊 檢測摘要:
  總 NS 數量: 8
  成功: 6
  失敗: 1
  未知: 1
  解析一致性: ❌ 不一致
  白名單驗證: ❌ 有 IP 未通過
  異常檢測: ⚠️  檢測到異常

⚠️  異常分析:
  - 發現不在白名單中的 IP: 203.0.113.1
  - 不同 NS 解析到不同的 IP，可能存在 DNS 劫持或污染
  - 1 個 NS 解析失敗，可能存在 DNS 污染
```

## 🔧 整合到監控系統

### Nagios/Icinga 配置

```bash
# Nagios command 定義
define command {
    command_name    check_dns_multi_ns
    command_line    /usr/local/bin/dns_checker_multi_ns.py \
                    -R $ARG1$ \
                    -W $ARG2$ \
                    --format nagios
}

# Service 定義
define service {
    service_description    DNS Check - example.com
    check_command          check_dns_multi_ns!example.com!whitelist.txt
    ...
}
```

### Prometheus 整合

```python
# 可以擴展工具以導出 Prometheus 指標
from prometheus_client import Counter, Gauge

dns_anomalies_total = Counter('dns_anomalies_total', 'Total DNS anomalies detected')
dns_consistency = Gauge('dns_consistency', 'DNS resolution consistency across NS')
```

### Cron 定時檢查

```bash
# 每 5 分鐘檢查一次
*/5 * * * * /usr/local/bin/dns_checker_multi_ns.py \
  -R example.com \
  -W whitelist.txt \
  --format json \
  >> /var/log/dns_check.log 2>&1
```

## 🚨 告警策略

### 告警級別

1. **CRITICAL**（退出碼 2）
   - 有 IP 不在白名單中
   - 不同 NS 解析結果不一致
   - 需要立即處理

2. **WARNING**（可擴展）
   - 部分 NS 解析失敗（但仍有成功的）
   - 可能需要關注

3. **UNKNOWN**（退出碼 3）
   - 所有 NS 都解析失敗
   - 可能是網絡問題或域名不存在

### 告警規則建議

```yaml
# 告警規則範例
rules:
  - alert: DNSHijacking
    expr: dns_anomalies_total{type="hijacking"} > 0
    for: 2m
    annotations:
      summary: "檢測到 DNS 劫持"
      
  - alert: DNSPollution
    expr: dns_anomalies_total{type="pollution"} > 0
    for: 5m
    annotations:
      summary: "檢測到 DNS 污染"
      
  - alert: DNSInconsistency
    expr: dns_consistency == 0
    for: 3m
    annotations:
      summary: "DNS 解析結果不一致"
```

## 💡 最佳實踐

1. **使用多個不同 ISP 的 NS**
   - 避免使用同一 ISP 的多個 NS
   - 建議使用：Google DNS、Cloudflare DNS、Quad9、OpenDNS

2. **定期更新白名單**
   - 當合法 IP 變更時，及時更新白名單
   - 使用版本控制管理白名單

3. **設置合理的超時時間**
   - 默認 5 秒，可根據網絡情況調整
   - 太短可能誤報，太長影響檢測速度

4. **監控趨勢**
   - 記錄歷史檢測結果
   - 分析異常模式
   - 建立基線

5. **自動化響應**
   - 檢測到異常時自動告警
   - 可以整合自動修復流程（如切換 DNS）

---

**最後更新**：2025-01-XX

