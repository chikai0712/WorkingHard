# Globalping API 額度說明

## 📊 額度類型

### 1. Rate Limit（速率限制）
- **用途**: 防止短時間內過多請求
- **限制**: 每分鐘 500 次測量
- **重置**: 滾動窗口，每分鐘重置
- **檢查**: `rateLimit.measurements.create.remaining`

### 2. Credits（信用額度）
- **用途**: 月度總使用量限制
- **限制**: 根據帳戶類型（免費/付費）
- **重置**: 每月初重置
- **檢查**: `credits.remaining`

## ⚠️ 當前狀態分析

你的 API 回應：
```json
{
  "rateLimit": {
    "measurements": {
      "create": {
        "type": "user",
        "limit": 500,
        "remaining": 404,
        "reset": 3418
      }
    }
  },
  "credits": {
    "remaining": 0
  }
}
```

### 解讀

1. **Rate Limit**: 404 / 500 ✅
   - 每分鐘還有 404 次可用
   - 這個會每分鐘重置

2. **Credits**: 0 ❌
   - **月度額度已用完**
   - 需要等到下個月才會重置
   - 或升級到付費計劃

## 🚨 重要發現

**即使 Rate Limit 有剩餘，如果 Credits = 0，API 仍然會拒絕請求。**

這就是為什麼智能檢測腳本判斷額度不足的原因。

## 💡 解決方案

### 選項 1：等待月度重置

- **時間**: 每月 1 日
- **費用**: 免費
- **額度**: 恢復到初始值

### 選項 2：升級付費計劃

訪問：https://globalping.io/pricing

**付費計劃優勢**：
- 更高的月度額度
- 更高的速率限制
- 優先支援

### 選項 3：優化使用（臨時方案）

如果只是測試功能：

1. **減少測試域名**
   ```bash
   # 只測試 2-3 個域名
   echo "google.com" > test.txt
   echo "facebook.com" >> test.txt
   ```

2. **減少探測節點**
   - 從 3 個節點減少到 1 個
   - 修改腳本中的 `"limit": 3` 改為 `"limit": 1`

3. **降低檢測頻率**
   - 從每 10 分鐘改為每天一次
   - 或每週一次

## 🔧 修改腳本以檢查 Credits

更新智能檢測腳本，同時檢查 Rate Limit 和 Credits：

```bash
# 檢查兩種額度
RATE_REMAINING=$(echo "$RESPONSE" | python3 -c '
import sys, json
data = json.load(sys.stdin)
print(data["rateLimit"]["measurements"]["create"]["remaining"])
')

CREDITS_REMAINING=$(echo "$RESPONSE" | python3 -c '
import sys, json
data = json.load(sys.stdin)
print(data["credits"]["remaining"])
')

echo "📊 Rate Limit: $RATE_REMAINING / 500"
echo "💰 Credits: $CREDITS_REMAINING"

if [ "$CREDITS_REMAINING" -eq 0 ]; then
    echo "❌ 月度額度已用完"
    echo "💡 請等待下個月或升級計劃"
    exit 0
fi
```

## 📅 額度重置時間表

| 類型 | 重置週期 | 重置時間 |
|------|---------|---------|
| **Rate Limit** | 每分鐘 | 滾動窗口 |
| **Credits** | 每月 | 每月 1 日 00:00 UTC |

## 💰 成本估算

### 免費計劃
- 月度額度: 10,000 次測量
- 速率限制: 100 次/分鐘（無 Token）或 500 次/分鐘（有 Token）

### 付費計劃
- 起價: $10/月
- 月度額度: 100,000+ 次測量
- 速率限制: 1,000+ 次/分鐘

## 🎯 建議

### 短期（本月）
1. 暫停自動檢測
2. 等待下個月額度重置
3. 或升級到付費計劃

### 長期
1. 監控額度使用情況
2. 優化檢測頻率
3. 考慮付費計劃（如果需要頻繁檢測）

## 📊 額度使用優化

### 計算每次檢測消耗

```bash
域名數量: 100
每個域名探測節點: 3
每次檢測消耗: 100 × 3 = 300 次測量
```

### 優化方案

1. **減少探測節點**: 3 → 1
   - 每次消耗: 100 次
   - 可執行次數: 100 次/月

2. **減少域名數量**: 100 → 50
   - 每次消耗: 150 次（3 節點）
   - 可執行次數: 66 次/月

3. **降低檢測頻率**: 每 10 分鐘 → 每天
   - 每月執行: 30 次
   - 每次消耗: 300 次
   - 總消耗: 9,000 次（在額度內）

---

**結論**: 你的月度額度已用完，需要等到下個月或升級計劃才能繼續使用。
