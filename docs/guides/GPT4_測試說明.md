# GPT-4.0 域名檢測分析工具

## 快速開始

### 方法 1: 一鍵執行（推薦）

```bash
# 設置 OpenAI API Key（只需執行一次）
export OPENAI_API_KEY='your-api-key-here'

# 執行測試（檢測 + GPT-4 分析）
~/Desktop/Project/test_10_domains_with_gpt4.sh
```

### 方法 2: 分步執行

#### 步驟 1: 檢測域名
```bash
~/Desktop/Project/id_globalping_auto_retry.sh ~/Desktop/Project/test_10_domains.txt
```

#### 步驟 2: GPT-4 分析
```bash
# 找到最新的日誌文件
LOG_FILE=$(ls -t ~/globalping_*.log | head -1)

# 使用 GPT-4 分析
python3 ~/Desktop/Project/gpt4_domain_analyzer.py "$LOG_FILE"
```

## 測試域名列表

當前測試的 10 個域名：
1. 78wwin.com
2. 1bez.com
3. 789wwin.live
4. 789wwin.fun
5. 789wwin.vip
6. 78wwin.fun
7. 78wwin.club
8. 111onlines.com
9. 5lionsbet.com
10. bajitop.com

## 功能特點

### 域名檢測腳本
- ✅ 使用 GlobalPing API 從印尼 3 個節點檢測
- ✅ 自動重試失敗的域名
- ✅ 智能延遲避免 API 頻率限制
- ✅ 完整的狀態分類（CLEAN/BLOCKED/TIMEOUT/WARNING/PARTIAL）
- ✅ 詳細的日誌記錄

### GPT-4.0 分析
- 🤖 使用 GPT-4.0 進行智能分析
- 📊 生成專業的分析報告
- 🎯 提供可執行的建議
- 🔍 風險評估和影響分析
- 📈 監控建議和告警閾值

## 輸出文件

執行後會生成兩個文件：

1. **檢測日誌**: `~/globalping_MMDD_HHMM.log`
   - 包含每個域名的詳細檢測結果
   - 節點信息、IP 地址、HTTP 狀態碼

2. **GPT-4 分析報告**: `~/globalping_MMDD_HHMM_gpt4_analysis.txt`
   - 執行摘要
   - 詳細分析
   - 風險評估
   - 技術建議
   - 監控建議

## 環境要求

### Python 依賴
```bash
pip3 install openai
```

### OpenAI API Key

獲取 API Key：https://platform.openai.com/api-keys

設置方式：

**臨時設置（當前終端）：**
```bash
export OPENAI_API_KEY='sk-xxx...'
```

**永久設置（推薦）：**
```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
echo "export OPENAI_API_KEY='sk-xxx...'" >> ~/.zshrc
source ~/.zshrc
```

## 使用場景

### 場景 1: 快速測試新域名
```bash
# 編輯域名列表
nano ~/Desktop/Project/test_10_domains.txt

# 執行測試
~/Desktop/Project/test_10_domains_with_gpt4.sh
```

### 場景 2: 分析現有日誌
```bash
# 如果已經有檢測日誌，直接分析
python3 ~/Desktop/Project/gpt4_domain_analyzer.py ~/globalping_1215_1430.log
```

### 場景 3: 批量測試多個域名文件
```bash
# 測試不同的域名集合
~/Desktop/Project/id_globalping_auto_retry.sh ~/domains_set1.txt
python3 ~/Desktop/Project/gpt4_domain_analyzer.py ~/globalping_*.log

~/Desktop/Project/id_globalping_auto_retry.sh ~/domains_set2.txt
python3 ~/Desktop/Project/gpt4_domain_analyzer.py ~/globalping_*.log
```

## 費用說明

- **GlobalPing API**: 免費（有頻率限制）
- **GPT-4.0 API**: 
  - 輸入: $0.03 / 1K tokens
  - 輸出: $0.06 / 1K tokens
  - 每次分析約 $0.10 - $0.30

## 故障排除

### 問題 1: API Key 錯誤
```
❌ GPT-4 API 調用失敗: Incorrect API key provided
```

**解決方案：**
- 檢查 API Key 是否正確
- 確認 API Key 有效且有餘額
- 重新設置環境變數

### 問題 2: 找不到 openai 模組
```
ModuleNotFoundError: No module named 'openai'
```

**解決方案：**
```bash
pip3 install openai
```

### 問題 3: GlobalPing API 頻率限制
```
❌ 檢測失敗 (API_ERROR)
```

**解決方案：**
- 腳本會自動重試
- 如果仍然失敗，等待 5-10 分鐘後重試
- 或增加 `DELAY` 參數（編輯腳本）

## 進階配置

### 調整檢測延遲
編輯 `id_globalping_auto_retry.sh`：
```bash
DELAY=8              # 每個域名間隔（秒）
API_ERROR_DELAY=30   # API 錯誤後延遲（秒）
BATCH_SIZE=30        # 每批域名數
BATCH_DELAY=60       # 批次間休息（秒）
```

### 自定義 GPT-4 分析
編輯 `gpt4_domain_analyzer.py` 中的 `prompt` 變數，可以：
- 調整分析重點
- 增加特定的分析維度
- 修改輸出格式

## 示例輸出

### 檢測日誌示例
```
🔍 檢測域名 [1/10]: 78wwin.com ...
  📍 PT Telekomunikasi Indonesia (AS7713) [Jakarta]
     🔌 節點IP: 202.134.0.155    | 🎯 目標IP: 104.21.45.123   | [CLEAN] ✅ 正常連通 (HTTP 200)
  📍 XL Axiata (AS24203) [Surabaya]
     🔌 節點IP: 202.152.0.45     | 🎯 目標IP: 104.21.45.123   | [CLEAN] ✅ 正常連通 (HTTP 200)
  📍 Indosat Ooredoo (AS4761) [Bandung]
     🔌 節點IP: 202.155.0.88     | 🎯 目標IP: 104.21.45.123   | [CLEAN] ✅ 正常連通 (HTTP 200)
  -> 整體狀態: CLEAN
```

### GPT-4 分析示例
```
📊 執行摘要
✅ 總體健康狀況：良好
🎯 關鍵發現：
  1. 80% 域名正常運作
  2. 發現 2 個域名完全超時
  3. 1 個域名存在區域性問題
⚠️ 緊急程度：中

🔍 詳細分析
...（GPT-4 生成的詳細分析）

💡 技術建議
短期措施：
  1. 立即檢查超時域名的 DNS 配置
  2. 監控部分異常域名的可用性
...
```

## 相關文件

- `test_10_domains.txt` - 測試域名列表
- `id_globalping_auto_retry.sh` - 域名檢測腳本
- `gpt4_domain_analyzer.py` - GPT-4 分析腳本
- `test_10_domains_with_gpt4.sh` - 一鍵執行腳本

## 更新日誌

### v1.0 (2024-12-15)
- ✅ 初始版本
- ✅ 支持 10 個域名測試
- ✅ 整合 GPT-4.0 分析
- ✅ 一鍵執行功能
