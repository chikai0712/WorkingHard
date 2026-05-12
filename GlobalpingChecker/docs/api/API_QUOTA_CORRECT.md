# ✅ Globalping API 額度機制（正確版本）

## 📊 額度類型

### 1. Rate Limit（速率限制）

**未認證用戶**：
- 每小時 250 次測試
- 每次測量 50 個探測器

**已認證用戶（使用 Token）**：
- 每小時 500 次測試
- 每次測量 500 個探測器

**重置機制**：
- 每小時滾動重置
- `reset` 字段顯示剩餘秒數

### 2. Credits（積分）

**用途**：
- 當超過每小時速率限制時使用
- 每次超額測試消耗 1 個積分

**獲取方式**：
- 訪問 https://globalping.io/credits
- 購買或通過其他方式獲得

## 🎯 你的當前狀態

```json
{
  "rateLimit": {
    "measurements": {
      "create": {
        "type": "user",
        "limit": 500,        // 每小時限制
        "remaining": 2,      // 本小時剩餘
        "reset": 3418        // 秒後重置
      }
    }
  },
  "credits": {
    "remaining": 0         // 積分餘額
  }
}
```

### 解讀

1. **Rate Limit**: 2 / 500
   - 本小時已使用 498 次
   - 還剩 2 次機會
   - 約 57 分鐘後重置到 500

2. **Credits**: 0
   - 積分已用完
   - 無法超額使用

## ⏰ 重置時間計算

```bash
# reset = 3418 秒
3418 秒 = 56.97 分鐘 ≈ 57 分鐘

# 所以大約 1 小時後，額度會重置到 500
```

## 💡 使用策略

### 當前可用額度：2 次

**選項 1：立即測試（2 個域名）**
```bash
# 創建測試文件
echo "google.com" > test.txt
echo "facebook.com" >> test.txt

# 執行測試
bash smart-check.sh test.txt
```

**選項 2：等待額度重置（推薦）**
- 等待約 1 小時
- 額度重置到 500
- 可以檢測更多域名

### 智能檢測策略

我已將閾值更新為 **50**：
- 當額度 >= 50 時才執行檢測
- 確保有足夠額度完成檢測
- 避免檢測到一半額度用完

## 📊 額度計算

### 每次檢測消耗

```bash
域名數量: 100
每個域名探測節點: 3
每次檢測消耗: 100 × 3 = 300 次測量
```

### 每小時可執行次數

```bash
每小時額度: 500
每次消耗: 300
可執行次數: 500 / 300 = 1.67 次/小時
```

### 建議檢測頻率

```bash
# 方案 1：每 2 小時檢測一次
*/120 * * * * cd ~/globalping-checker && bash smart-check.sh domains.txt

# 方案 2：每小時檢測一次（減少域名到 150 個）
0 * * * * cd ~/globalping-checker && bash smart-check.sh domains.txt

# 方案 3：每 10 分鐘智能檢測（推薦）
*/10 * * * * cd ~/globalping-checker && bash smart-check.sh domains.txt
```

## 🔧 優化建議

### 1. 減少探測節點

從 3 個減少到 2 個：
```bash
# 在檢測腳本中
"limit": 2  # 從 3 改為 2
```

**效果**：
- 每次消耗: 100 × 2 = 200 次
- 可執行次數: 500 / 200 = 2.5 次/小時

### 2. 分批檢測

將域名分成多批：
```bash
# 第 1 批：前 50 個域名
head -50 domains.txt > batch1.txt

# 第 2 批：後 50 個域名
tail -50 domains.txt > batch2.txt

# 交替檢測
0 * * * * bash smart-check.sh batch1.txt
30 * * * * bash smart-check.sh batch2.txt
```

### 3. 動態調整

根據域名數量自動調整：
```bash
DOMAIN_COUNT=$(wc -l < domains.txt)
PROBES_PER_DOMAIN=3
NEEDED=$((DOMAIN_COUNT * PROBES_PER_DOMAIN))

if [ "$REMAINING" -ge "$NEEDED" ]; then
    # 額度充足，執行檢測
    bash id_globalping_multi_v3.3_Telegram.sh domains.txt
else
    echo "額度不足，需要 $NEEDED，剩餘 $REMAINING"
fi
```

## 📅 重置時間表

| 時間 | 額度狀態 |
|------|---------|
| 現在 | 2 / 500 |
| +57 分鐘 | 500 / 500（重置）|
| +1 小時 | 500 / 500 |
| +2 小時 | 500 / 500（再次重置）|

## 🎯 最佳實踐

### 1. 使用智能檢測

```bash
# 設置閾值為 50
QUOTA_THRESHOLD=50

# 每 10 分鐘檢查
*/10 * * * * bash smart-check.sh domains.txt
```

### 2. 監控額度使用

```bash
# 檢測前後記錄額度
echo "檢測前: $(curl -s -H 'Authorization: Bearer TOKEN' https://api.globalping.io/v1/limits)"
bash id_globalping_multi_v3.3_Telegram.sh domains.txt
echo "檢測後: $(curl -s -H 'Authorization: Bearer TOKEN' https://api.globalping.io/v1/limits)"
```

### 3. 設置告警

當額度低於閾值時發送通知：
```bash
if [ "$REMAINING" -lt 100 ]; then
    send_telegram_message "⚠️ API 額度不足: $REMAINING / 500"
fi
```

## 💰 獲取更多額度

### 選項 1：等待重置
- 免費
- 每小時自動重置

### 選項 2：購買積分
- 訪問 https://globalping.io/credits
- 用於超額使用

### 選項 3：優化使用
- 減少探測節點
- 降低檢測頻率
- 分批檢測

---

**總結**：你的每小時額度即將重置（約 57 分鐘後），屆時會恢復到 500 次。建議設置智能檢測，當額度 >= 50 時自動執行。
