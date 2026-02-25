# 🧪 DNS 檢測功能測試指南

## 📋 測試目標

驗證優化後的 DNS 檢測邏輯：
- ✅ 雙指標判斷（resolution_rate vs whitelist_match_rate）
- ✅ 統一 50% 閾值
- ✅ 白名單可選功能
- ✅ 錯誤分級（error vs warning）
- ✅ 告警去重和自動恢復

---

## 🚀 步驟 1：重啟服務

```bash
cd /Users/ckchiu/Desktop/Project/domain-monitoring-system

# 重啟所有服務
docker-compose restart api celery-worker celery-beat

# 確認服務狀態
docker-compose ps
```

預期輸出：所有服務都是 `Up` 狀態

---

## 🔍 步驟 2：查看日誌

### 2.1 查看 Celery Worker 日誌
```bash
docker-compose logs -f celery-worker
```

**觀察重點**：
- 每 5 分鐘執行 `check_all_domains`
- 日誌格式：`Checked domain xxx.com: ok (resolution: 80.0%, whitelist: 60.0%)`
- 確認顯示雙指標

### 2.2 查看 Celery Beat 日誌
```bash
docker-compose logs -f celery-beat
```

**觀察重點**：
- 確認任務調度正常
- 每 5 分鐘觸發 DNS 檢查

---

## 📊 步驟 3：測試場景

### 場景 1：正常域名（有白名單）

**測試域名**：google.com
**預期 IP**：設定白名單（例如：142.250.x.x）

**預期結果**：
```
resolution_rate: 100%（所有 DNS 都能解析）
whitelist_match_rate: 100%（IP 在白名單內）
status: ok
```

**日誌範例**：
```
Checked domain google.com: ok (resolution: 100.0%, whitelist: 100.0%)
```

---

### 場景 2：正常域名（無白名單）

**測試域名**：example.com
**預期 IP**：None 或空

**預期結果**：
```
resolution_rate: 100%（所有 DNS 都能解析）
whitelist_match_rate: 0%（無白名單）
has_whitelist: False
status: ok（使用 resolution_rate 判斷）
```

**日誌範例**：
```
Checked domain example.com: ok (resolution: 100.0%, whitelist: 0.0%)
```

---

### 場景 3：白名單不匹配

**測試域名**：google.com
**預期 IP**：錯誤的 IP（例如：1.1.1.1）

**預期結果**：
```
resolution_rate: 100%（DNS 能解析）
whitelist_match_rate: 0%（IP 不在白名單）
status: warning
告警級別: P3（whitelist_mismatch）
```

**日誌範例**：
```
Checked domain google.com: warning (resolution: 100.0%, whitelist: 0.0%)
Created and sent alert for google.com: whitelist_mismatch
```

---

### 場景 4：無 DNS 記錄

**測試域名**：nonexistent-domain-12345.com

**預期結果**：
```
resolution_rate: 0%（無法解析）
whitelist_match_rate: 0%
status: warning
告警級別: P2（config_error）
```

**日誌範例**：
```
Checked domain nonexistent-domain-12345.com: warning (resolution: 0.0%, whitelist: 0.0%)
Created and sent alert for nonexistent-domain-12345.com: config_error
```

---

### 場景 5：部分 DNS 失敗

**測試條件**：5 個 DNS 伺服器，3 個成功，2 個失敗

**預期結果**：
```
resolution_rate: 60%（3/5）
status: ok（>= 50%）
```

**日誌範例**：
```
Checked domain example.com: ok (resolution: 60.0%, whitelist: 60.0%)
```

---

## 🎯 步驟 4：驗證告警功能

### 4.1 查看告警列表
```bash
# 訪問告警頁面
open http://localhost:8000/alerts.html
```

**檢查項目**：
- ✅ 告警是否正確創建
- ✅ 告警級別是否正確（P0/P1/P2/P3）
- ✅ 證據摘要是否清楚
- ✅ 相同告警是否去重（只更新 last_seen）

### 4.2 測試告警恢復
1. 修復問題域名（例如：修正白名單）
2. 等待下一次檢查（最多 5 分鐘）
3. 確認告警自動標記為已解決

**日誌範例**：
```
Checked domain google.com: ok (resolution: 100.0%, whitelist: 100.0%)
Resolved 1 alerts for domain 123
```

---

## 🔧 步驟 5：測試手動檢測

### 5.1 訪問暫停域名頁面
```bash
open http://localhost:8000/paused-domains.html
```

### 5.2 點擊「🔍 立即檢測無記錄域名」

**預期行為**：
- 檢測所有啟用的域名
- 無法解析的域名暫停到明天 0:00
- 顯示檢測結果（檢查數量、暫停數量）

**日誌範例**：
```
Checking 100 domains for DNS records
Paused domain nonexistent.com until next midnight (no DNS records)
Daily check completed: 0 domains unpaused, 100 domains checked, 5 domains paused
```

---

## 📈 步驟 6：查看監控事件

### 6.1 訪問儀表板
```bash
open http://localhost:8000/
```

### 6.2 查看最近事件

**檢查項目**：
- ✅ 事件類型正確（dns_check）
- ✅ 狀態正確（ok/warning）
- ✅ 詳細信息包含雙指標
- ✅ 域名顯示正確（不是 Domain #ID）

---

## 🐛 步驟 7：檢查錯誤處理

### 7.1 模擬 DNS 伺服器全部不健康
```sql
-- 在資料庫中標記所有 DNS 為不健康
UPDATE nameservers SET is_healthy = false;
```

**預期行為**：
- 日誌顯示：`No healthy nameservers available`
- 不會崩潰，正常記錄錯誤

### 7.2 恢復 DNS 伺服器
```sql
UPDATE nameservers SET is_healthy = true;
```

---

## ✅ 驗證清單

### DNS 檢測核心
- [ ] 雙指標正確顯示（resolution_rate, whitelist_match_rate）
- [ ] 50% 閾值正確應用
- [ ] 有白名單時使用 whitelist_match_rate 判斷
- [ ] 無白名單時使用 resolution_rate 判斷
- [ ] 日誌格式正確且詳細

### 錯誤分級
- [ ] DNS 錯誤標記為 severity: error
- [ ] 白名單不匹配標記為 severity: warning
- [ ] 只有真正的 DNS 錯誤才觸發 P2 告警

### 告警功能
- [ ] P3 白名單不匹配告警正確創建
- [ ] 相同告警正確去重（更新 last_seen）
- [ ] 狀態恢復時自動解決告警
- [ ] 告警通知正確發送

### 暫停功能
- [ ] 手動檢測功能正常
- [ ] 無記錄域名正確暫停到明天 0:00
- [ ] 暫停域名不參與 5 分鐘檢測
- [ ] 每天 0:00 正確重置暫停狀態

---

## 📝 測試記錄模板

```
測試日期：____________________
測試人員：____________________

場景 1 - 正常域名（有白名單）
- 域名：____________________
- resolution_rate：_____%
- whitelist_match_rate：_____%
- 狀態：____________________
- 結果：✅ / ❌

場景 2 - 正常域名（無白名單）
- 域名：____________________
- resolution_rate：_____%
- 狀態：____________________
- 結果：✅ / ❌

場景 3 - 白名單不匹配
- 域名：____________________
- 告警級別：____________________
- 告警根因：____________________
- 結果：✅ / ❌

場景 4 - 無 DNS 記錄
- 域名：____________________
- 告警級別：____________________
- 結果：✅ / ❌

場景 5 - 告警恢復
- 域名：____________________
- 恢復時間：____________________
- 結果：✅ / ❌

總體評價：____________________
發現問題：____________________
```

---

## 🔍 常用調試命令

```bash
# 查看最近 100 行日誌
docker-compose logs --tail=100 celery-worker

# 實時監控日誌
docker-compose logs -f celery-worker | grep "Checked domain"

# 查看特定域名的日誌
docker-compose logs celery-worker | grep "example.com"

# 進入容器查看
docker-compose exec api bash

# 手動觸發檢查（在容器內）
python -c "from app.tasks import check_all_domains; check_all_domains()"

# 查看資料庫
docker-compose exec db psql -U postgres -d domain_monitoring
```

---

## 💡 預期優化效果

優化前 vs 優化後對比：

| 項目 | 優化前 | 優化後 |
|------|--------|--------|
| 日誌信息 | `status: ok` | `ok (resolution: 80%, whitelist: 60%)` |
| 白名單不匹配 | P2 錯誤 | P3 警告 |
| 成功率閾值 | 80% | 50% |
| 無白名單域名 | 可能誤報 | 正確判斷 |
| 告警準確性 | 較多誤報 | 精確告警 |

---

## 🎯 測試完成標準

✅ 所有場景測試通過
✅ 日誌顯示雙指標
✅ 告警級別正確
✅ 無誤報或漏報
✅ 性能正常（5 分鐘內完成所有檢查）

測試通過後，可以繼續整合 uptime 和 SecurityTrails 功能！

