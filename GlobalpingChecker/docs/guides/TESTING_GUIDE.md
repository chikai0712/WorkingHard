# Globalping 腳本測試指南

## 📝 測試準備

### 1. 創建測試文件

```bash
cd ~/Desktop/Project/GlobalpingChecker

# 創建包含 2 個域名的測試文件
cat > test_2_domains.txt << 'EOF'
7plusmm.com
diamonds9bet.com
EOF

# 確認文件內容
cat test_2_domains.txt
```

---

## 🧪 測試所有腳本版本

### 測試 v3.0（推薦）

```bash
cd ~/Desktop/Project/GlobalpingChecker

# 執行 v3.0
./id_globalping_auto_retry.sh test_2_domains.txt
```

**預計時間**: 約 30 秒  
**特點**: 
- 延遲 8 秒（最穩定）
- 自動禁用代理
- 顯示節點詳細信息（ASN、城市、節點IP）

---

### 測試 v2.1

```bash
cd ~/Desktop/Project/GlobalpingChecker

# 執行 v2.1
./id_globalping_multi_v2.1.sh test_2_domains.txt
```

**預計時間**: 約 25 秒  
**特點**:
- 延遲 5 秒
- 有 CSV 導出
- 自動重試

---

### 測試 v2.0

```bash
cd ~/Desktop/Project/GlobalpingChecker

# 執行 v2.0
./id_globalping_multi_v2.sh test_2_domains.txt
```

**預計時間**: 約 20 秒  
**特點**:
- 延遲 4 秒（最快）
- 有 CSV 導出

---

### 測試 v4.0（CLI 版本）

```bash
cd ~/Desktop/Project/GlobalpingChecker

# 執行 v4.0
./id_globalping_cli.sh test_2_domains.txt
```

**預計時間**: 約 25 秒  
**特點**:
- 使用官方 CLI
- 需要 API 配額

---

## 📊 查看測試結果

### 查看實時輸出

測試時會直接在終端顯示結果，例如：

```
🔍 檢測域名 [1/2]: 7plusmm.com ...
  📍 BIZNET NETWORKS (AS17451) [Jakarta]
     🎯 目標IP: 1.2.3.4  | [CLEAN] ✅ 正常連通 (HTTP 301)
  ...
```

### 查看日誌文件

```bash
# 查看最新的日誌
ls -lt ~/globalping*.log | head -5

# 查看 v3.0 日誌
tail -50 ~/globalping_*.log

# 查看 v2.1 日誌
tail -50 ~/globalping_multi_*.log

# 查看 v4.0 日誌
tail -50 ~/globalping_cli_*.log
```

### 查看 CSV 文件（v2.0/v2.1）

```bash
# 查看 CSV 文件
ls -lt ~/globalping_multi_*.csv | head -1

# 用 Excel 或 Numbers 打開
open ~/globalping_multi_*.csv
```

---

## 🔍 對比測試結果

### 測試所有版本並對比

```bash
cd ~/Desktop/Project/GlobalpingChecker

echo "=== 測試 v3.0 ==="
./id_globalping_auto_retry.sh test_2_domains.txt
echo ""
sleep 10

echo "=== 測試 v2.1 ==="
./id_globalping_multi_v2.1.sh test_2_domains.txt
echo ""
sleep 10

echo "=== 測試 v2.0 ==="
./id_globalping_multi_v2.sh test_2_domains.txt
```

---

## ⚠️ 注意事項

### 1. API 配額

每次測試消耗：
- 2 個域名 × 3 個節點 = **6 credits**

免費配額約 100-200 credits，可以測試約 **15-30 次**

### 2. 延遲時間

為避免觸發限制，建議：
- 每次測試間隔 **10 秒以上**
- 使用 v3.0（延遲最長，最穩定）

### 3. 錯誤處理

如果看到 `API_ERROR`：
- 等待 15-20 分鐘
- 或明天再測試

---

## 📈 預期結果

### 成功的輸出

```
🔍 檢測域名 [1/2]: 7plusmm.com ...
  📍 BIZNET NETWORKS (AS17451) [Jakarta]
     🎯 目標IP: 107.167.190.204  | [CLEAN] ✅ 正常連通 (HTTP 308)
  📍 Media Sarana Data (AS45727) [Surabaya]
     🎯 目標IP: 107.167.190.204  | [CLEAN] ✅ 正常連通 (HTTP 308)
  📍 XL Axiata (AS24203) [Jakarta]
     🎯 目標IP: 107.167.190.204  | [CLEAN] ✅ 正常連通 (HTTP 308)
  -> 整體狀態: CLEAN
------------------------------------------------

🔍 檢測域名 [2/2]: diamonds9bet.com ...
  📍 BIZNET NETWORKS (AS17451) [Jakarta]
     🎯 目標IP: 104.21.56.214  | [CLEAN] ✅ 正常連通 (HTTP 301)
  📍 Media Sarana Data (AS45727) [Surabaya]
     🎯 目標IP: 104.21.56.214  | [CLEAN] ✅ 正常連通 (HTTP 301)
  📍 XL Axiata (AS24203) [Jakarta]
     🎯 目標IP: 104.21.56.214  | [CLEAN] ✅ 正常連通 (HTTP 301)
  -> 整體狀態: CLEAN
------------------------------------------------

========================================
檢測完成
========================================
✅ 正常連通 (CLEAN):   2
🚨 DNS 污染 (BLOCKED): 0
⚠️  完全超時 (TIMEOUT): 0
⚠️  服務異常 (WARNING): 0
🔄 部分異常 (PARTIAL): 0
❌ 檢測失敗 (API_ERROR): 0
========================================
```

---

## 🎯 推薦測試順序

1. **先測試 v3.0**（最穩定）
2. 等待 10 秒
3. **測試 v2.1**（有 CSV）
4. 等待 10 秒
5. **測試 v2.0**（速度快）

---

## 💡 快速測試命令

```bash
# 一鍵創建測試文件並執行 v3.0
cd ~/Desktop/Project/GlobalpingChecker && \
echo -e "7plusmm.com\ndiamonds9bet.com" > test_2_domains.txt && \
./id_globalping_auto_retry.sh test_2_domains.txt
```

---

**現在就可以開始測試了！** 🚀
