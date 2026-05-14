# 數據庫使用指南

## 📚 概述

本項目使用 SQLite 數據庫存儲域名檢測結果，支持：
- 歷史記錄查詢
- 趨勢分析
- 批次對比
- 數據導出

## 🗄️ 數據庫結構

### 表結構

#### 1. test_batches（測試批次表）
存儲每次測試的摘要信息

| 欄位 | 類型 | 說明 |
|------|------|------|
| batch_id | INTEGER | 批次 ID（主鍵） |
| test_date | DATETIME | 測試時間 |
| total_domains | INTEGER | 總域名數 |
| clean_count | INTEGER | 正常域名數 |
| blocked_count | INTEGER | 被封鎖域名數 |
| timeout_count | INTEGER | 超時域名數 |
| warning_count | INTEGER | 異常域名數 |
| partial_count | INTEGER | 部分異常域名數 |
| api_error_count | INTEGER | API 錯誤數 |
| log_file | TEXT | 日誌文件路徑 |
| notes | TEXT | 備註 |

#### 2. domain_results（域名結果表）
存儲每個域名的測試結果

| 欄位 | 類型 | 說明 |
|------|------|------|
| result_id | INTEGER | 結果 ID（主鍵） |
| batch_id | INTEGER | 批次 ID（外鍵） |
| domain | TEXT | 域名 |
| overall_status | TEXT | 整體狀態 |
| test_date | DATETIME | 測試時間 |

#### 3. node_details（節點詳情表）
存儲每個測試節點的詳細信息

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

## 🚀 快速開始

### 方法 1：一鍵測試並保存（推薦）

```bash
# 基本用法
./run_test_and_save.sh test_2_domains.txt

# 帶備註
./run_test_and_save.sh test_10_domains.txt "每日定時檢測"

# 完整測試
./run_test_and_save.sh domains.txt "完整測試 - 2026-03-06"
```

這個腳本會自動：
1. ✅ 執行域名檢測
2. ✅ 保存結果到數據庫
3. ✅ 顯示統計信息
4. ✅ 生成 CSV 文件

### 方法 2：手動分步執行

```bash
# 步驟 1：執行測試
./id_globalping_multi_v3.1_Token.sh test_2_domains.txt

# 步驟 2：保存到數據庫
python3 save_to_db.py ~/globalping_0306_1234.log "測試備註"

# 步驟 3：查看結果
python3 view_db.py list
```

## 📊 查詢數據

### 1. 列出所有測試批次

```bash
python3 view_db.py list
```

輸出範例：
```
================================================================================
📊 所有測試批次
================================================================================

批次 ID: 3
測試時間: 2026-03-06 14:30:00
總域名數: 10
  ✅ CLEAN:     8 (80.0%)
  🚨 BLOCKED:   1 (10.0%)
  ⚠️  TIMEOUT:   1 (10.0%)
  ⚠️  WARNING:   0 (0.0%)
  🔄 PARTIAL:   0 (0.0%)
  ❌ API_ERROR: 0
備註: 每日定時檢測
日誌: /Users/xxx/globalping_0306_1430.log
--------------------------------------------------------------------------------
```

### 2. 查看特定批次詳情

```bash
python3 view_db.py show <batch_id>
```

範例：
```bash
python3 view_db.py show 3
```

### 3. 查詢特定域名

```bash
# 查詢最新結果
python3 view_db.py domain example.com

# 查詢特定批次的結果
python3 view_db.py domain example.com --batch 3
```

### 4. 查看統計信息

```bash
# 所有測試的統計
python3 view_db.py stats

# 特定批次的統計
python3 view_db.py stats --batch 3
```

輸出包括：
- 按狀態統計
- 按 ISP 統計 BLOCKED 數量
- 按城市統計 BLOCKED 數量

### 5. 對比兩個批次

```bash
python3 view_db.py compare <batch_id1> <batch_id2>
```

範例：
```bash
python3 view_db.py compare 1 3
```

輸出：
- 狀態變化對比
- 新增的 BLOCKED 域名
- 恢復的域名（從 BLOCKED 變為 CLEAN）

## 📈 使用場景

### 場景 1：每日定時監控

```bash
# 每天執行
./run_test_and_save.sh domains.txt "每日檢測 $(date +%Y-%m-%d)"

# 查看趨勢
python3 view_db.py list
```

### 場景 2：問題域名追蹤

```bash
# 查詢特定域名的歷史
python3 view_db.py domain problem-domain.com

# 查看詳細節點信息
python3 view_db.py domain problem-domain.com --batch 3
```

### 場景 3：ISP 封鎖分析

```bash
# 查看哪些 ISP 封鎖最多
python3 view_db.py stats

# 查看特定批次的 ISP 統計
python3 view_db.py stats --batch 3
```

### 場景 4：批次對比

```bash
# 對比今天和昨天的結果
python3 view_db.py compare 5 6

# 查看新增的封鎖域名
```

## 📤 數據導出

### 導出 CSV

測試完成後會自動生成 CSV 文件：
```
test_results_batch_<batch_id>.csv
```

CSV 包含：
- 域名
- 整體狀態
- ISP
- ASN
- 城市
- 節點 IP
- 目標 IP
- 節點狀態
- HTTP 狀態碼

### 手動導出

如果需要重新導出：

```python
from save_to_db import GlobalpingDB

db = GlobalpingDB()
db.export_to_csv(batch_id=3, output_file='custom_export.csv')
db.close()
```

## 🔧 進階使用

### 直接 SQL 查詢

```bash
sqlite3 globalping_results.db
```

常用查詢：

```sql
-- 查看最近 5 次測試
SELECT batch_id, test_date, total_domains, blocked_count 
FROM test_batches 
ORDER BY test_date DESC 
LIMIT 5;

-- 查找一直被封鎖的域名
SELECT domain, COUNT(*) as blocked_times
FROM domain_results
WHERE overall_status = 'BLOCKED'
GROUP BY domain
HAVING blocked_times > 3
ORDER BY blocked_times DESC;

-- 查看特定 ISP 的封鎖情況
SELECT dr.domain, nd.node_city, nd.target_ip
FROM domain_results dr
JOIN node_details nd ON dr.result_id = nd.result_id
WHERE nd.node_isp LIKE '%XL Axiata%'
AND dr.overall_status = 'BLOCKED';

-- 統計每個城市的封鎖率
SELECT 
    nd.node_city,
    COUNT(*) as total_tests,
    SUM(CASE WHEN dr.overall_status = 'BLOCKED' THEN 1 ELSE 0 END) as blocked_count,
    ROUND(SUM(CASE WHEN dr.overall_status = 'BLOCKED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as blocked_rate
FROM domain_results dr
JOIN node_details nd ON dr.result_id = nd.result_id
GROUP BY nd.node_city
ORDER BY blocked_rate DESC;
```

## 🔄 數據維護

### 備份數據庫

```bash
# 備份
cp globalping_results.db globalping_results_backup_$(date +%Y%m%d).db

# 壓縮備份
tar -czf globalping_db_$(date +%Y%m%d).tar.gz globalping_results.db
```

### 清理舊數據

```sql
-- 刪除 30 天前的數據
DELETE FROM test_batches 
WHERE test_date < datetime('now', '-30 days');

-- 清理孤立的記錄
DELETE FROM domain_results 
WHERE batch_id NOT IN (SELECT batch_id FROM test_batches);

DELETE FROM node_details 
WHERE result_id NOT IN (SELECT result_id FROM domain_results);

-- 優化數據庫
VACUUM;
```

## 📊 數據可視化（未來擴展）

可以使用以下工具進行可視化：

1. **Grafana + SQLite 插件**
   - 實時監控面板
   - 趨勢圖表

2. **Python + Matplotlib**
   - 生成統計圖表
   - 封鎖趨勢分析

3. **Jupyter Notebook**
   - 交互式數據分析
   - 深度挖掘

## ❓ 常見問題

### Q1: 數據庫文件在哪裡？
A: 默認在項目根目錄：`globalping_results.db`

### Q2: 如何遷移到 PostgreSQL？
A: 可以使用 `pgloader` 或手動導出/導入：
```bash
# 導出 SQLite
sqlite3 globalping_results.db .dump > dump.sql

# 導入 PostgreSQL（需要調整 SQL 語法）
psql -U username -d database < dump.sql
```

### Q3: 數據庫太大怎麼辦？
A: 
- 定期清理舊數據
- 執行 VACUUM 優化
- 考慮分表或遷移到 PostgreSQL

### Q4: 如何自動化測試？
A: 使用 cron 定時任務：
```bash
# 編輯 crontab
crontab -e

# 每天早上 9 點執行
0 9 * * * cd /path/to/GlobalpingChecker && ./run_test_and_save.sh domains.txt "每日自動檢測"
```

## 📝 總結

使用數據庫存儲測試結果的優勢：
- ✅ 歷史記錄追蹤
- ✅ 趨勢分析
- ✅ 批次對比
- ✅ 靈活查詢
- ✅ 數據導出
- ✅ 易於備份

開始使用：
```bash
# 1. 執行測試並保存
./run_test_and_save.sh test_2_domains.txt "第一次測試"

# 2. 查看結果
python3 view_db.py list

# 3. 查看統計
python3 view_db.py stats
```
