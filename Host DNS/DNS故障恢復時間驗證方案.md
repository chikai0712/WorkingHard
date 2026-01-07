# DNS 故障恢復時間驗證方案

## 一、測試目標

驗證當權威 DNS 伺服器異常時，玩家連線恢復正常的時間（Time to Recovery, TTR），包括：
1. **DNS 查詢失敗檢測時間**：玩家端首次發現 DNS 異常的時間
2. **DNS 快取失效時間**：DNS 解析器快取中的記錄過期時間
3. **故障轉移時間**：切換到備用權威 DNS 的時間
4. **連線恢復時間**：玩家能夠成功連線到服務的總時間

---

## 二、測試環境準備

### 2.1 測試架構

```
測試場景：
┌─────────────┐
│   玩家端     │
│  (客戶端)    │
└──────┬──────┘
       │ DNS 查詢
       ↓
┌─────────────────────────────────┐
│    遞迴DNS解析器 (Recursive)     │
│  (Cloudflare, Google, ISP)      │
└──────┬──────────────────────────┘
       │
       ↓
┌─────────────────────────────────┐
│     權威DNS伺服器 (Authoritative) │
│  ┌──────────┐  ┌──────────┐     │
│  │ Primary  │  │Secondary │     │
│  │   (主)   │  │   (備)   │     │
│  └────┬─────┘  └────┬─────┘     │
└───────┼─────────────┼───────────┘
        │             │
    [故障模擬]    [正常運作]
```

### 2.2 測試工具

| 工具 | 用途 | 說明 |
|------|------|------|
| **dig / nslookup** | DNS 查詢測試 | 測試 DNS 解析是否正常 |
| **tcpdump / Wireshark** | 網路封包抓取 | 監控 DNS 查詢封包 |
| **PowerDNS / BIND** | 權威 DNS 伺服器 | 可模擬故障場景 |
| **Python / Bash 腳本** | 自動化測試 | 持續監控 DNS 狀態 |
| **Grafana / Prometheus** | 監控儀表板 | 視覺化 DNS 狀態指標 |
| **Chaos Engineering 工具** | 故障注入 | 模擬 DNS 伺服器故障 |

---

## 三、測試場景設計

### 3.1 場景一：單一權威 DNS 故障（無備用）

**測試目的**：驗證當只有一個權威 DNS 時，故障後的恢復時間

**測試步驟**：
1. 設置單一權威 DNS 伺服器（Primary）
2. 設定 DNS TTL = 300 秒（5分鐘）
3. 玩家端進行 DNS 查詢，確認正常運作
4. 模擬故障：停止 Primary DNS 服務
5. 持續監控玩家端的 DNS 查詢狀態
6. 記錄故障檢測時間（首次查詢失敗）
7. 記錄恢復時間（DNS TTL 到期後，查詢持續失敗）

**預期結果**：
- **故障檢測時間**：立即（首次查詢即失敗）
- **恢復時間**：無恢復（單點故障，需要手動修復）
- **影響範圍**：所有新查詢立即失敗，快取記錄在 TTL 到期前仍可用

---

### 3.2 場景二：主備權威 DNS（Primary-Secondary）

**測試目的**：驗證主備切換的恢復時間

**測試步驟**：
1. 設置主備架構（Primary + Secondary）
2. 設定 DNS TTL = 60 秒（1分鐘）
3. 配置 Secondary 為備用，通過 AXFR/IXFR 同步記錄
4. 玩家端進行 DNS 查詢，確認正常運作
5. 模擬故障：停止 Primary DNS 服務
6. 持續監控：
   - Secondary 是否自動接管
   - 玩家端 DNS 查詢狀態
   - DNS 記錄同步狀態
7. 記錄關鍵時間點：
   - Primary 故障時間
   - Secondary 接管時間（如果自動）
   - 玩家端查詢恢復時間

**預期結果**：
- **故障檢測時間**：遞迴 DNS 解析器檢測到 Primary 無回應（約 1-5 秒）
- **切換時間**：
  - **手動切換**：取決於管理員操作（通常 5-30 分鐘）
  - **自動切換**：需要健康檢查機制（通常 30-120 秒）
- **恢復時間**：切換完成後，新查詢立即恢復（快取記錄需等待 TTL 到期）

---

### 3.3 場景三：Anycast DNS（多個節點）

**測試目的**：驗證 Anycast DNS 故障後的流量自動重新路由時間

**測試步驟**：
1. 設置 Anycast DNS（多個地理位置的節點）
2. 設定 DNS TTL = 300 秒（5分鐘）
3. 玩家端從不同地理位置進行 DNS 查詢
4. 模擬故障：
   - 單個節點故障（部分地區受影響）
   - 多個節點故障（全局影響）
5. 監控：
   - BGP 路由更新時間
   - DNS 查詢流量重新路由時間
   - 玩家端查詢恢復時間

**預期結果**：
- **單節點故障**：
  - **路由更新時間**：BGP 收斂時間（通常 30-90 秒）
  - **流量重新路由**：自動切換到其他節點
  - **玩家影響**：部分地區短暫中斷（30-90 秒）
- **多節點故障**：
  - **影響範圍**：取決於剩餘節點數量
  - **恢復時間**：取決於節點修復時間

---

### 3.4 場景四：DNS TTL 對恢復時間的影響

**測試目的**：驗證不同 TTL 設定對故障恢復時間的影響

**測試步驟**：
1. 設置主備 DNS 架構
2. 測試不同 TTL 設定：
   - TTL = 60 秒（短 TTL，快速失效）
   - TTL = 300 秒（中等 TTL，5分鐘）
   - TTL = 3600 秒（長 TTL，1小時）
3. 模擬 Primary DNS 故障
4. 記錄快取記錄失效時間
5. 記錄玩家端查詢恢復時間

**預期結果**：

| TTL 設定 | 快取失效時間 | 影響說明 |
|---------|------------|---------|
| 60 秒 | 1 分鐘內 | 快速失效，但增加 DNS 查詢頻率 |
| 300 秒 | 5 分鐘內 | 平衡點，故障影響約 5 分鐘 |
| 3600 秒 | 1 小時內 | 長時間快取，故障影響可達 1 小時 |

---

## 四、測試指標定義

### 4.1 關鍵時間指標（KPI）

| 指標 | 定義 | 測量方法 | 目標值 |
|------|------|---------|--------|
| **MTTD**<br>(Mean Time To Detect) | 平均故障檢測時間 | 從故障發生到首次檢測到異常的時間 | < 30 秒 |
| **MTTR**<br>(Mean Time To Repair) | 平均修復時間 | 從故障發生到服務恢復的時間 | < 5 分鐘 |
| **DNS 查詢失敗率** | 查詢失敗的百分比 | 失敗查詢數 / 總查詢數 × 100% | < 1% |
| **快取命中率** | 快取命中查詢的百分比 | 快取命中數 / 總查詢數 × 100% | > 80% |
| **RTT 延遲** | DNS 查詢往返時間 | 查詢請求到回應的時間 | < 100 ms |

### 4.2 監控指標

- **DNS 查詢量**：每秒查詢數（QPS）
- **DNS 回應時間**：查詢延遲（ms）
- **DNS 錯誤率**：SERVFAIL、NXDOMAIN 等錯誤比例
- **伺服器健康狀態**：CPU、記憶體、網路連線狀態
- **同步狀態**：主備 DNS 記錄同步狀態

---

## 五、測試執行方案

### 5.1 測試腳本範例（Python）

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNS 故障恢復時間測試腳本
"""

import dns.resolver
import time
import datetime
import json
from typing import List, Dict

class DNSTestResult:
    def __init__(self):
        self.start_time = None
        self.failure_time = None
        self.recovery_time = None
        self.query_results = []
    
    def record_query(self, domain: str, success: bool, latency: float):
        """記錄 DNS 查詢結果"""
        result = {
            "timestamp": datetime.datetime.now().isoformat(),
            "domain": domain,
            "success": success,
            "latency_ms": latency
        }
        self.query_results.append(result)
        return result

def test_dns_resolution(domain: str, nameserver: str = None) -> tuple[bool, float]:
    """
    測試 DNS 解析
    
    Returns:
        (success: bool, latency_ms: float)
    """
    resolver = dns.resolver.Resolver()
    if nameserver:
        resolver.nameservers = [nameserver]
    
    start_time = time.time()
    try:
        answers = resolver.resolve(domain, 'A', lifetime=5)
        latency = (time.time() - start_time) * 1000
        return True, latency
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        print(f"DNS 查詢失敗: {domain}, 錯誤: {e}")
        return False, latency

def continuous_monitoring(domain: str, interval: int = 5, duration: int = 300):
    """
    持續監控 DNS 狀態
    
    Args:
        domain: 測試域名
        interval: 查詢間隔（秒）
        duration: 監控持續時間（秒）
    """
    result = DNSTestResult()
    result.start_time = datetime.datetime.now()
    
    print(f"開始監控 DNS: {domain}")
    print(f"查詢間隔: {interval} 秒，持續時間: {duration} 秒")
    print("-" * 60)
    
    failure_detected = False
    recovery_detected = False
    
    end_time = time.time() + duration
    query_count = 0
    
    while time.time() < end_time:
        query_count += 1
        success, latency = test_dns_resolution(domain)
        query_result = result.record_query(domain, success, latency)
        
        # 檢測故障
        if not success and not failure_detected:
            result.failure_time = datetime.datetime.now()
            failure_detected = True
            print(f"[故障檢測] {result.failure_time.strftime('%H:%M:%S')} - DNS 查詢失敗")
        
        # 檢測恢復
        if success and failure_detected and not recovery_detected:
            result.recovery_time = datetime.datetime.now()
            recovery_detected = True
            downtime = (result.recovery_time - result.failure_time).total_seconds()
            print(f"[恢復檢測] {result.recovery_time.strftime('%H:%M:%S')} - DNS 查詢恢復")
            print(f"[恢復時間] 故障持續時間: {downtime:.2f} 秒")
        
        status = "✓" if success else "✗"
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {status} 查詢 #{query_count}: {latency:.2f}ms")
        
        time.sleep(interval)
    
    # 統計結果
    total_queries = len(result.query_results)
    successful_queries = sum(1 for q in result.query_results if q["success"])
    failed_queries = total_queries - successful_queries
    failure_rate = (failed_queries / total_queries * 100) if total_queries > 0 else 0
    avg_latency = sum(q["latency_ms"] for q in result.query_results) / total_queries if total_queries > 0 else 0
    
    print("-" * 60)
    print("測試結果統計:")
    print(f"總查詢數: {total_queries}")
    print(f"成功查詢: {successful_queries} ({100-failure_rate:.2f}%)")
    print(f"失敗查詢: {failed_queries} ({failure_rate:.2f}%)")
    print(f"平均延遲: {avg_latency:.2f}ms")
    
    if result.failure_time and result.recovery_time:
        downtime = (result.recovery_time - result.failure_time).total_seconds()
        print(f"故障恢復時間: {downtime:.2f} 秒 ({downtime/60:.2f} 分鐘)")
    elif result.failure_time:
        print(f"故障檢測時間: {result.failure_time.strftime('%H:%M:%S')}")
        print("狀態: 尚未恢復")
    
    return result

if __name__ == "__main__":
    # 測試參數
    TEST_DOMAIN = "example.com"  # 替換為實際測試域名
    QUERY_INTERVAL = 5  # 每 5 秒查詢一次
    TEST_DURATION = 600  # 測試持續 10 分鐘
    
    # 執行測試
    result = continuous_monitoring(TEST_DOMAIN, QUERY_INTERVAL, TEST_DURATION)
    
    # 保存結果到 JSON 文件
    output_file = f"dns_test_result_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "start_time": result.start_time.isoformat() if result.start_time else None,
            "failure_time": result.failure_time.isoformat() if result.failure_time else None,
            "recovery_time": result.recovery_time.isoformat() if result.recovery_time else None,
            "query_results": result.query_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n測試結果已保存到: {output_file}")
```

### 5.2 測試腳本範例（Bash）

```bash
#!/bin/bash
# DNS 故障恢復時間測試腳本（Bash 版本）

DOMAIN="example.com"
INTERVAL=5  # 查詢間隔（秒）
DURATION=600  # 測試持續時間（秒）
LOG_FILE="dns_test_$(date +%Y%m%d_%H%M%S).log"

echo "開始 DNS 故障恢復時間測試"
echo "域名: $DOMAIN"
echo "查詢間隔: ${INTERVAL}秒"
echo "持續時間: ${DURATION}秒"
echo "日誌檔案: $LOG_FILE"
echo "----------------------------------------"

FAILURE_TIME=""
RECOVERY_TIME=""
FAILURE_DETECTED=false
RECOVERY_DETECTED=false
QUERY_COUNT=0
SUCCESS_COUNT=0
FAIL_COUNT=0

start_time=$(date +%s)
end_time=$((start_time + DURATION))

while [ $(date +%s) -lt $end_time ]; do
    QUERY_COUNT=$((QUERY_COUNT + 1))
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 執行 DNS 查詢
    if dig +short +timeout=5 $DOMAIN @8.8.8.8 > /dev/null 2>&1; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        STATUS="✓"
        
        # 檢測恢復
        if [ "$FAILURE_DETECTED" = true ] && [ "$RECOVERY_DETECTED" = false ]; then
            RECOVERY_TIME=$TIMESTAMP
            RECOVERY_DETECTED=true
            downtime=$(($(date +%s) - $(date -d "$FAILURE_TIME" +%s)))
            echo "[恢復檢測] $RECOVERY_TIME - DNS 查詢恢復" | tee -a "$LOG_FILE"
            echo "[恢復時間] 故障持續時間: ${downtime} 秒 ($(($downtime / 60)) 分鐘)" | tee -a "$LOG_FILE"
        fi
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
        STATUS="✗"
        
        # 檢測故障
        if [ "$FAILURE_DETECTED" = false ]; then
            FAILURE_TIME=$TIMESTAMP
            FAILURE_DETECTED=true
            echo "[故障檢測] $FAILURE_TIME - DNS 查詢失敗" | tee -a "$LOG_FILE"
        fi
    fi
    
    echo "[$TIMESTAMP] $STATUS 查詢 #$QUERY_COUNT" | tee -a "$LOG_FILE"
    sleep $INTERVAL
done

# 統計結果
FAILURE_RATE=$(awk "BEGIN {printf \"%.2f\", ($FAIL_COUNT / $QUERY_COUNT) * 100}")
echo "----------------------------------------"
echo "測試結果統計:"
echo "總查詢數: $QUERY_COUNT"
echo "成功查詢: $SUCCESS_COUNT ($(awk "BEGIN {printf \"%.2f\", 100-$FAILURE_RATE}")%)"
echo "失敗查詢: $FAIL_COUNT ($FAILURE_RATE%)"
echo "----------------------------------------"

if [ -n "$FAILURE_TIME" ] && [ -n "$RECOVERY_TIME" ]; then
    downtime=$(($(date -d "$RECOVERY_TIME" +%s) - $(date -d "$FAILURE_TIME" +%s)))
    echo "故障恢復時間: ${downtime} 秒 ($(($downtime / 60)) 分鐘)"
elif [ -n "$FAILURE_TIME" ]; then
    echo "故障檢測時間: $FAILURE_TIME"
    echo "狀態: 尚未恢復"
fi
```

---

## 六、故障模擬方法

### 6.1 使用 iptables 阻擋 DNS 流量

```bash
# 阻擋 DNS 查詢（Port 53）
sudo iptables -A INPUT -p udp --dport 53 -j DROP
sudo iptables -A INPUT -p tcp --dport 53 -j DROP

# 恢復 DNS 查詢
sudo iptables -D INPUT -p udp --dport 53 -j DROP
sudo iptables -D INPUT -p tcp --dport 53 -j DROP
```

### 6.2 停止 DNS 服務

```bash
# BIND DNS
sudo systemctl stop named

# PowerDNS
sudo systemctl stop pdns

# 恢復服務
sudo systemctl start named
sudo systemctl start pdns
```

### 6.3 使用 Chaos Engineering 工具

**Chaos Monkey** 或 **Chaos Mesh** 可用於：
- 隨機停止 DNS 服務
- 模擬網路延遲
- 模擬服務崩潰

---

## 七、測試報告範本

### 7.1 測試結果報告格式

```markdown
# DNS 故障恢復時間測試報告

## 測試資訊
- **測試日期**: 2025-12-16
- **測試環境**: 生產環境（或測試環境）
- **測試域名**: example.com
- **DNS 架構**: Primary-Secondary（主備）

## 測試場景
- **場景**: 主備權威 DNS（Primary-Secondary）
- **TTL 設定**: 300 秒（5分鐘）
- **故障類型**: Primary DNS 服務停止

## 測試結果

### 關鍵時間指標
| 指標 | 時間 | 說明 |
|------|------|------|
| 故障發生時間 | 10:00:00 | Primary DNS 服務停止 |
| 故障檢測時間 (MTTD) | 10:00:03 | 3 秒後檢測到異常 |
| Secondary 接管時間 | 10:00:45 | 45 秒後 Secondary 接管 |
| 查詢恢復時間 | 10:00:48 | 48 秒後查詢恢復 |
| 總恢復時間 (MTTR) | 48 秒 | 故障發生到恢復的總時間 |

### 統計數據
- **總查詢數**: 120
- **成功查詢**: 115 (95.83%)
- **失敗查詢**: 5 (4.17%)
- **平均查詢延遲**: 45ms
- **最大查詢延遲**: 5200ms（故障期間）

### 影響分析
- **影響範圍**: 所有新 DNS 查詢在故障期間失敗
- **快取影響**: TTL 300 秒內的快取記錄仍可使用
- **用戶影響**: 部分用戶可能在 5 分鐘內無法連線（取決於快取）

## 結論與建議

1. **恢復時間符合目標**: MTTR = 48 秒 < 5 分鐘目標
2. **建議縮短 TTL**: 將 TTL 從 300 秒降至 60 秒，可減少故障影響時間
3. **建議添加自動健康檢查**: 實現自動故障轉移，進一步縮短恢復時間
```

---

## 八、最佳實踐建議

### 8.1 DNS 架構建議

1. **多層備援**：
   - 至少 2 個權威 DNS 伺服器（主備）
   - 部署在不同地理位置（提高可用性）
   - 使用 Anycast（自動流量重新路由）

2. **健康檢查機制**：
   - 實現自動健康檢查（每 30 秒檢查一次）
   - 自動故障轉移（檢測到故障後自動切換）

3. **TTL 設定**：
   - 平衡快取時間和故障恢復時間
   - 建議 TTL = 60-300 秒（1-5 分鐘）
   - 故障時可臨時降低 TTL（預先設定）

### 8.2 監控建議

1. **即時監控**：
   - DNS 查詢量（QPS）
   - DNS 錯誤率
   - DNS 回應時間（RTT）

2. **告警機制**：
   - DNS 查詢失敗率 > 1% 時告警
   - DNS 回應時間 > 500ms 時告警
   - DNS 伺服器健康狀態異常時告警

3. **定期測試**：
   - 每月執行一次故障恢復測試
   - 驗證備用 DNS 是否正常運作
   - 驗證自動故障轉移機制

---

## 附錄：參考資料

- **DNS TTL 最佳實踐**: [RFC 2308](https://tools.ietf.org/html/rfc2308)
- **DNS 故障轉移**: [RFC 2136](https://tools.ietf.org/html/rfc2136) (DNS Update)
- **Anycast DNS**: [RFC 4786](https://tools.ietf.org/html/rfc4786)
- **DNS 健康檢查**: [RFC 8767](https://tools.ietf.org/html/rfc8767) (Service Binding)

