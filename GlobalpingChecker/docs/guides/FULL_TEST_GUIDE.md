# 完整域名測試執行指南

## 🎯 測試流程

### 第一步：執行 v3.0 測試

```bash
cd ~/Desktop/Project/GlobalpingChecker

# 執行完整測試（498 個域名）
./id_globalping_multi_v3.0.sh ~/Documents/domains.txt
```

**預計時間**: 70-90 分鐘  
**消耗配額**: 498 × 3 = 1494 credits

---

### 第二步：等待測試完成

測試過程中會顯示：
```
🔍 檢測域名 [1/498]: example.com ...
  📍 BIZNET NETWORKS (AS17451) [Jakarta]
     🔌 節點IP: xxx.xxx.xxx.xxx  | 🎯 目標IP: xxx.xxx.xxx.xxx  | [CLEAN] ✅
  ...
```

---

### 第三步：查找日誌文件

```bash
# 查找最新的日誌文件
ls -lt ~/globalping_*.log | head -1

# 或直接查看
LOG_FILE=$(ls -t ~/globalping_*.log | head -1)
echo "日誌文件: $LOG_FILE"
```

---

### 第四步：保存到數據庫

```bash
cd ~/Desktop/Project/GlobalpingChecker

# 保存測試結果到數據庫
python3 save_to_db.py ~/globalping_0305_1800.log "第一次完整測試"
```

**輸出範例**：
```
📖 解析日誌文件: /Users/ckchiu/globalping_0305_1800.log
✅ 數據庫初始化完成
✅ 創建測試批次 ID: 1
✅ 保存完成：498 個域名

============================================================
📊 測試結果摘要
============================================================
測試時間: 2026-03-05 18:00:00
總域名數: 498
✅ 正常連通 (CLEAN):   450
🚨 DNS 污染 (BLOCKED): 30
⚠️  完全超時 (TIMEOUT): 10
⚠️  服務異常 (WARNING): 5
🔄 部分異常 (PARTIAL): 3
❌ 檢測失敗 (API_ERROR): 0
============================================================

🚨 DNS 污染域名列表：
  - blocked-site1.com
  - blocked-site2.com
  ...

✅ 完成！批次 ID: 1
📊 數據庫: globalping_results.db
📄 CSV 文件: test_results_batch_1.csv
```

---

## 📊 查看測試結果

### 方法 1: 查看 CSV 文件

```bash
# 用 Excel 或 Numbers 打開
open test_results_batch_1.csv
```

**CSV 包含欄位**：
- 域名
- 整體狀態
- ISP
- ASN
- 城市
- 節點IP
- 目標IP
- 節點狀態
- HTTP狀態碼

---

### 方法 2: 查詢數據庫

```bash
# 進入 SQLite
sqlite3 globalping_results.db

# 查看所有測試批次
SELECT * FROM test_batches;

# 查看 BLOCKED 域名
SELECT domain FROM domain_results WHERE overall_status = 'BLOCKED';

# 查看特定域名的詳細信息
SELECT * FROM domain_results WHERE domain = 'example.com';

# 退出
.quit
```

---

### 方法 3: Python 查詢

```python
import sqlite3

conn = sqlite3.connect('globalping_results.db')
cursor = conn.cursor()

# 查詢 BLOCKED 域名
cursor.execute("""
    SELECT domain, overall_status 
    FROM domain_results 
    WHERE overall_status = 'BLOCKED'
""")

for row in cursor.fetchall():
    print(f"{row[0]} - {row[1]}")

conn.close()
```

---

## 🗄️ 數據庫結構

### 表 1: test_batches（測試批次）

| 欄位 | 類型 | 說明 |
|------|------|------|
| batch_id | INTEGER | 批次 ID（主鍵） |
| test_date | DATETIME | 測試時間 |
| total_domains | INTEGER | 總域名數 |
| clean_count | INTEGER | CLEAN 數量 |
| blocked_count | INTEGER | BLOCKED 數量 |
| timeout_count | INTEGER | TIMEOUT 數量 |
| warning_count | INTEGER | WARNING 數量 |
| partial_count | INTEGER | PARTIAL 數量 |
| api_error_count | INTEGER | API_ERROR 數量 |
| log_file | TEXT | 日誌文件路徑 |
| notes | TEXT | 備註 |

---

### 表 2: domain_results（域名結果）

| 欄位 | 類型 | 說明 |
|------|------|------|
| result_id | INTEGER | 結果 ID（主鍵） |
| batch_id | INTEGER | 批次 ID（外鍵） |
| domain | TEXT | 域名 |
| overall_status | TEXT | 整體狀態 |
| test_date | DATETIME | 測試時間 |

---

### 表 3: node_details（節點詳情）

| 欄位 | 類型 | 說明 |
|------|------|------|
| detail_id | INTEGER | 詳情 ID（主鍵） |
| result_id | INTEGER | 結果 ID（外鍵） |
| node_isp | TEXT | ISP 名稱 |
| node_asn | TEXT | ASN 號碼 |
| node_city | TEXT | 城市 |
| node_ip | TEXT | 節點 IP |
| target_ip | TEXT | 目標 IP |
| status | TEXT | 節點狀態 |
| http_code | TEXT | HTTP 狀態碼 |

---

## 📈 常用查詢

### 1. 查看所有測試批次

```sql
SELECT 
    batch_id,
    test_date,
    total_domains,
    clean_count,
    blocked_count
FROM test_batches
ORDER BY test_date DESC;
```

---

### 2. 查看 BLOCKED 域名及其目標 IP

```sql
SELECT 
    dr.domain,
    nd.target_ip,
    nd.node_isp,
    nd.node_city
FROM domain_results dr
JOIN node_details nd ON dr.result_id = nd.result_id
WHERE dr.overall_status = 'BLOCKED'
GROUP BY dr.domain;
```

---

### 3. 統計各 ISP 的 BLOCKED 數量

```sql
SELECT 
    nd.node_isp,
    COUNT(DISTINCT dr.domain) as blocked_count
FROM domain_results dr
JOIN node_details nd ON dr.result_id = nd.result_id
WHERE dr.overall_status = 'BLOCKED'
GROUP BY nd.node_isp
ORDER BY blocked_count DESC;
```

---

### 4. 查看特定域名的所有節點測試結果

```sql
SELECT 
    nd.node_isp,
    nd.node_city,
    nd.node_ip,
    nd.target_ip,
    nd.status,
    nd.http_code
FROM domain_results dr
JOIN node_details nd ON dr.result_id = nd.result_id
WHERE dr.domain = 'example.com';
```

---

## 🔄 後續測試

### 定期測試（建議每週一次）

```bash
# 執行測試
./id_globalping_multi_v3.0.sh ~/Documents/domains.txt

# 保存到數據庫
python3 save_to_db.py ~/globalping_MMDD_HHMM.log "第二次測試"
```

### 對比不同批次

```sql
-- 對比兩次測試的 BLOCKED 數量
SELECT 
    batch_id,
    test_date,
    blocked_count
FROM test_batches
ORDER BY test_date;

-- 查看新增的 BLOCKED 域名
SELECT domain 
FROM domain_results 
WHERE batch_id = 2 AND overall_status = 'BLOCKED'
AND domain NOT IN (
    SELECT domain 
    FROM domain_results 
    WHERE batch_id = 1 AND overall_status = 'BLOCKED'
);
```

---

## ⚠️ 注意事項

### 1. API 配額

**免費配額**：100-200 credits/天  
**需要配額**：498 × 3 = 1494 credits

**建議**：
- 註冊 Globalping 帳號（獲得 1000+ credits/天）
- 或分批測試（每天測試 100 個域名）

---

### 2. 測試時間

**完整測試**：70-90 分鐘  
**建議**：
- 在非工作時間執行
- 使用後台執行

```bash
# 後台執行
nohup ./id_globalping_multi_v3.0.sh ~/Documents/domains.txt > ~/test.out 2>&1 &

# 查看進度
tail -f ~/globalping_*.log
```

---

### 3. 數據備份

```bash
# 備份數據庫
cp globalping_results.db globalping_results_backup_$(date +%Y%m%d).db

# 備份 CSV
cp test_results_batch_*.csv ~/backups/
```

---

## 🚀 快速開始

```bash
# 1. 進入項目目錄
cd ~/Desktop/Project/GlobalpingChecker

# 2. 執行測試（後台）
nohup ./id_globalping_multi_v3.0.sh ~/Documents/domains.txt > ~/test.out 2>&1 &

# 3. 查看進度
tail -f ~/globalping_*.log

# 4. 測試完成後，保存到數據庫
LOG_FILE=$(ls -t ~/globalping_*.log | head -1)
python3 save_to_db.py "$LOG_FILE" "第一次完整測試"

# 5. 查看結果
open test_results_batch_1.csv
```

---

**準備好開始測試了嗎？** 🎯
