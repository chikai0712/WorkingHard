# 域名檢測工具套件使用指南

## 📦 工具清單

### 1. 錯誤分類系統文檔
**文件**: `domain-status-classification.md`
**用途**: 完整的狀態分類定義和實施指南

### 2. 改進版檢測腳本 v2.0
**文件**: `~/id_globalping_multi_v2.sh`
**用途**: 帶頻率控制、重試機制、進度顯示的域名檢測腳本

### 3. 結果分析工具
**文件**: `analyze_domain_results.py`
**用途**: 分析現有日誌，生成分類報告和 CSV

---

## 🚀 快速開始

### 步驟 1: 給腳本添加執行權限

```bash
chmod +x ~/id_globalping_multi_v2.sh
```

### 步驟 2: 運行改進版檢測腳本

```bash
# 基本用法
~/id_globalping_multi_v2.sh ~/domains.txt

# 腳本會自動生成以下文件：
# - ~/globalping_multi_MMDD_HHMM.log      # 詳細日誌
# - ~/globalping_multi_MMDD_HHMM.csv      # CSV 報告
# - ~/globalping_failed_MMDD_HHMM.txt     # 失敗域名清單
# - ~/globalping_summary_MMDD_HHMM.txt    # 摘要報告
```

### 步驟 3: 分析現有日誌（如果需要）

```bash
# 分析你之前的檢測結果
python3 analyze_domain_results.py ~/globalping_multi_1204_1530.log

# 或從標準輸入讀取
cat your_log.txt | python3 analyze_domain_results.py -
```

---

## 📊 改進版腳本 v2.0 的新特性

### ✨ 核心改進

1. **完整的狀態分類**
   - ✅ CLEAN: 正常連通
   - 🚨 BLOCKED: DNS 污染
   - ⚠️ TIMEOUT: 完全超時
   - ⚠️ WARNING: 服務異常
   - 🔄 PARTIAL: 部分節點異常
   - ❌ API_ERROR: 檢測失敗

2. **智能重試機制**
   - API 失敗自動重試（最多 3 次）
   - 指數退避策略（2秒 → 6秒 → 18秒）
   - 區分 API 錯誤和域名問題

3. **頻率控制**
   - 每個域名間延遲 4 秒（可配置）
   - 每 50 個域名休息 30 秒
   - API 錯誤後延遲 15 秒

4. **進度顯示**
   - 實時進度條：`進度: [45/100] (45%)`
   - 批次處理提示
   - 彩色狀態輸出

5. **完整報告**
   - 詳細日誌（每個節點的結果）
   - CSV 導出（便於 Excel 分析）
   - 摘要報告（統計和分類清單）
   - 失敗域名清單（便於重試）

### ⚙️ 可配置參數

在腳本開頭修改這些參數：

```bash
DELAY_BETWEEN_DOMAINS=4         # 每個域名之間的延遲（秒）
DELAY_AFTER_API_ERROR=15        # API 錯誤後的延遲（秒）
BATCH_SIZE=50                   # 批次大小
BATCH_DELAY=30                  # 批次間延遲（秒）
MAX_RETRIES=3                   # 最大重試次數
RETRY_BACKOFF_BASE=3            # 重試退避基數（秒）
API_WAIT_TIME=8                 # 等待 API 結果的時間（秒）
```

---

## 📋 輸出文件說明

### 1. 詳細日誌 (`.log`)

```
🔍 檢測域名 [1/100]: example.com ...
  📍 BIZNET NETWORKS          | IP: 1.2.3.4         | [CLEAN] ✅ 正常連通 (HTTP 301)
  📍 Media Sarana Data        | IP: 1.2.3.4         | [CLEAN] ✅ 正常連通 (HTTP 301)
  📍 XL Axiata                | IP: 1.2.3.4         | [CLEAN] ✅ 正常連通 (HTTP 301)
  -> 整體狀態: CLEAN
------------------------------------------------
```

### 2. CSV 報告 (`.csv`)

可用 Excel 打開，包含：
- 域名
- 整體狀態
- 每個節點的 ISP、IP、狀態碼、狀態

### 3. 摘要報告 (`.txt`)

```
========================================
域名檢測摘要報告
========================================
檢測時間: 2026-03-04 15:30:00
總域名數: 100
已處理: 100

========================================
狀態統計
========================================
✅ 正常連通 (CLEAN):     85 (85%)
🚨 DNS 污染 (BLOCKED):   5 (5%)
⚠️  完全超時 (TIMEOUT):   8 (8%)
...
```

### 4. 失敗域名清單 (`.txt`)

純文本列表，每行一個域名，可直接用於重試：

```
megawinner88.com
mm777global.online
mmbet388.com
...
```

---

## 🔄 重試失敗的域名

如果有域名因 API 限制失敗：

```bash
# 使用生成的失敗清單重新檢測
~/id_globalping_multi_v2.sh ~/globalping_failed_1204_1530.txt
```

---

## 📊 分析工具使用

### 基本用法

```bash
python3 analyze_domain_results.py <日誌文件>
```

### 輸出內容

1. **統計摘要**: 各狀態的數量和百分比
2. **分類清單**: 
   - DNS 污染域名
   - 完全超時域名
   - 部分異常域名
   - 服務異常域名
   - 檢測失敗域名
3. **建議動作**: 針對每種狀態的處理建議
4. **CSV 導出**: `*_analysis.csv`
5. **失敗清單**: `*_failed_domains.txt`

---

## 🎯 實際使用場景

### 場景 1: 首次大批量檢測

```bash
# 1. 準備域名列表
cat > ~/domains.txt << EOF
example1.com
example2.com
example3.com
EOF

# 2. 運行檢測
~/id_globalping_multi_v2.sh ~/domains.txt

# 3. 查看摘要
cat ~/globalping_summary_*.txt

# 4. 如果有失敗的域名，重新檢測
~/id_globalping_multi_v2.sh ~/globalping_failed_*.txt
```

### 場景 2: 分析舊日誌

```bash
# 分析之前的檢測結果
python3 analyze_domain_results.py ~/old_log.txt

# 查看生成的報告
cat old_log_analysis.csv
```

### 場景 3: 持續監控

```bash
# 每天定時檢測
crontab -e

# 添加：每天凌晨 2 點檢測
0 2 * * * /Users/ckchiu/id_globalping_multi_v2.sh /Users/ckchiu/domains.txt
```

---

## ⚠️ 注意事項

### API 頻率限制

Globalping API 有免費額度限制：
- 建議每個域名間隔 3-5 秒
- 大批量檢測時分批進行
- 遇到 API 錯誤會自動重試

### 結果解讀

1. **CLEAN (正常連通)**
   - HTTP 2xx/3xx/403 都算正常
   - 301/308 是重定向，不是錯誤
   - 只代表「連得上」，不代表內容正常

2. **BLOCKED (DNS 污染)**
   - 最嚴重，需要立即處理
   - ISP 層級封鎖
   - 需要更換域名或使用 CDN

3. **TIMEOUT (完全超時)**
   - 可能是域名配置問題
   - 可能是服務器關閉
   - 需要檢查 DNS 和服務器

4. **PARTIAL (部分異常)**
   - 區域性問題
   - 某些 ISP 有問題
   - 需要針對性處理

5. **WARNING (服務異常)**
   - HTTP 4xx/5xx
   - 不是封鎖，是網站本身問題
   - 需要檢查服務器

6. **API_ERROR (檢測失敗)**
   - 工具問題，不是域名問題
   - 需要重新檢測

---

## 🆚 新舊版本對比

| 功能 | 舊版本 | v2.0 |
|------|--------|------|
| 狀態分類 | 4 種 | 6 種（更細緻） |
| 重試機制 | ❌ | ✅ 智能重試 |
| 頻率控制 | 固定 2 秒 | ✅ 分級延遲 |
| 進度顯示 | ❌ | ✅ 實時進度條 |
| 批次處理 | ❌ | ✅ 自動分批 |
| 摘要報告 | ❌ | ✅ 完整統計 |
| CSV 導出 | ❌ | ✅ 結構化數據 |
| 失敗清單 | ❌ | ✅ 自動記錄 |
| 彩色輸出 | ❌ | ✅ 易於閱讀 |

---

## 🐛 故障排除

### 問題 1: 權限錯誤

```bash
chmod +x ~/id_globalping_multi_v2.sh
```

### 問題 2: Python 找不到

```bash
# 確認 Python 3 已安裝
which python3

# 如果沒有，安裝 Python 3
brew install python3  # macOS
```

### 問題 3: 大量 API 錯誤

調整配置參數，增加延遲：

```bash
# 編輯腳本
nano ~/id_globalping_multi_v2.sh

# 修改這些值
DELAY_BETWEEN_DOMAINS=6         # 增加到 6 秒
DELAY_AFTER_API_ERROR=20        # 增加到 20 秒
BATCH_SIZE=30                   # 減少到 30 個
```

### 問題 4: 結果不準確

- 重新檢測可疑域名
- 使用不同時間段檢測
- 對比多次檢測結果

---

## 📞 技術支援

如有問題，請檢查：
1. 日誌文件中的錯誤訊息
2. API 響應內容
3. 網絡連接狀態

---

## 📝 更新日誌

### v2.0 (2026-03-04)
- ✨ 新增完整的狀態分類系統
- ✨ 新增智能重試機制
- ✨ 新增頻率控制和批次處理
- ✨ 新增進度顯示
- ✨ 新增摘要報告和 CSV 導出
- ✨ 新增失敗域名自動記錄
- 🎨 改進輸出格式（彩色、對齊）
- 📝 完善文檔和使用指南

### v1.0 (原版)
- 基本的域名檢測功能
- 簡單的狀態判斷
- 日誌輸出

---

## 🎓 最佳實踐

1. **檢測前**
   - 確認域名列表格式正確
   - 預估檢測時間（約 5-10 秒/域名）
   - 確保網絡連接穩定

2. **檢測中**
   - 不要中斷腳本
   - 觀察進度和錯誤訊息
   - 如果大量 API 錯誤，考慮暫停

3. **檢測後**
   - 查看摘要報告
   - 優先處理 BLOCKED 和 TIMEOUT
   - 重新檢測失敗的域名
   - 定期監控重要域名

4. **報告使用**
   - CSV 用於數據分析
   - 摘要用於快速了解
   - 詳細日誌用於問題排查
   - 失敗清單用於重試

---

## 📚 相關文檔

- `domain-status-classification.md` - 完整的分類系統說明
- `~/id_globalping_multi_v2.sh` - 改進版檢測腳本
- `analyze_domain_results.py` - 結果分析工具

---

**祝檢測順利！** 🎉
