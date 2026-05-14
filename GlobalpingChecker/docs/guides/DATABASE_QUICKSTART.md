# 🚀 數據庫功能快速測試

## 立即測試

### 測試 1：執行檢測並保存到數據庫

```bash
cd ~/Desktop/Project/GlobalpingChecker
./run_test_and_save.sh test_2_domains.txt "第一次測試"
```

這個命令會：
1. ✅ 執行域名檢測（使用正確的 Token）
2. ✅ 自動保存結果到 SQLite 數據庫
3. ✅ 顯示統計信息
4. ✅ 生成 CSV 文件

### 測試 2：查看數據庫中的所有測試

```bash
python3 view_db.py list
```

### 測試 3：查看統計信息

```bash
python3 view_db.py stats
```

### 測試 4：查詢特定域名

```bash
python3 view_db.py domain 7plusmm.com
```

## 預期結果

### 執行測試時會看到：

```
========================================
域名檢測 + 數據庫保存
========================================
域名文件: test_2_domains.txt
數據庫: /Users/ckchiu/Desktop/Project/GlobalpingChecker/globalping_results.db
備註: 第一次測試

📡 步驟 1/4: 執行域名檢測...

========================================
域名檢測腳本 v3.1 - Token 版本
========================================
域名文件: test_2_domains.txt
總域名數: 2
延遲設置: 8秒/域名
自動重試: 啟用（最多 2 輪）
使用 Token: uh5vlg4ttg...
========================================

=== 域名檢測開始 ===
...

✅ 檢測完成，日誌文件: ~/globalping_0306_1234.log

💾 步驟 2/4: 保存結果到數據庫...

📖 解析日誌文件: ~/globalping_0306_1234.log
✅ 數據庫初始化完成
✅ 創建測試批次 ID: 1
✅ 保存完成：2 個域名

📊 步驟 3/4: 顯示統計信息...

📈 批次 1 統計信息
================================================================================

按狀態統計:
  CLEAN     :    2
  BLOCKED   :    0
  TIMEOUT   :    0

✅ 所有步驟完成
========================================

📊 數據庫文件: globalping_results.db
📄 日誌文件: ~/globalping_0306_1234.log
🆔 批次 ID: 1
📊 CSV 文件: test_results_batch_1.csv

常用查詢命令：
  # 查看所有測試批次
  python3 view_db.py list

  # 查看本次測試詳情
  python3 view_db.py show 1

  # 查看統計信息
  python3 view_db.py stats

  # 查詢特定域名
  python3 view_db.py domain <域名>
```

## 完整功能測試流程

```bash
# 1. 第一次測試（2個域名）
./run_test_and_save.sh test_2_domains.txt "測試-2域名"

# 2. 第二次測試（10個域名）
./run_test_and_save.sh test_10.txt "測試-10域名"

# 3. 查看所有批次
python3 view_db.py list

# 4. 查看第一個批次詳情
python3 view_db.py show 1

# 5. 查看第二個批次詳情
python3 view_db.py show 2

# 6. 對比兩個批次
python3 view_db.py compare 1 2

# 7. 查看統計信息
python3 view_db.py stats

# 8. 查詢特定域名
python3 view_db.py domain 7plusmm.com
```

## 文件說明

### 新增文件：

1. **run_test_and_save.sh** - 一鍵測試並保存腳本
   - 整合測試和數據庫保存
   - 自動生成統計報告

2. **DATABASE_GUIDE.md** - 數據庫使用完整指南
   - 數據庫結構說明
   - 查詢命令大全
   - 使用場景範例

### 現有文件（已存在）：

1. **save_to_db.py** - 數據庫保存工具
   - 解析日誌文件
   - 保存到 SQLite
   - 導出 CSV

2. **view_db.py** - 數據庫查詢工具
   - 查看批次
   - 統計分析
   - 批次對比

3. **id_globalping_multi_v3.1_Token.sh** - 域名檢測腳本（已修復 Token）
   - 使用正確的 Token: `uh5vlg4ttg3v5gwby5zgtqrciimahql5`
   - 每小時 500 次配額

## 數據庫優勢

✅ **歷史追蹤** - 保存所有測試記錄
✅ **趨勢分析** - 查看域名狀態變化
✅ **批次對比** - 對比不同時間的測試結果
✅ **靈活查詢** - SQL 查詢任意數據
✅ **數據導出** - 自動生成 CSV 文件
✅ **統計報告** - 按 ISP、城市統計封鎖情況

## 下一步

1. **立即測試**：
   ```bash
   ./run_test_and_save.sh test_2_domains.txt "第一次測試"
   ```

2. **查看結果**：
   ```bash
   python3 view_db.py list
   ```

3. **閱讀完整指南**：
   ```bash
   cat DATABASE_GUIDE.md
   ```

## 技術棧

- **數據庫**: SQLite 3
- **語言**: Python 3 + Bash
- **特點**: 
  - 零配置
  - 單文件數據庫
  - 易於備份和遷移
  - 支持複雜查詢
  - 可輕鬆遷移到 PostgreSQL

開始測試吧！🚀
