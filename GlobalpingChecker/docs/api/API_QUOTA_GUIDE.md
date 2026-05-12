# Globalping API 額度測試指令

## 🔍 快速檢查額度

### 方法 1：使用腳本（推薦）

```bash
cd ~/Desktop/Project/GlobalpingChecker
bash check-api-quota.sh
```

### 方法 2：直接使用 curl

```bash
# 設置你的 API Token
export GLOBALPING_TOKEN="gp_uh5vlg4ttg3v5gwby5zgtqrciimahql5"

# 查詢額度
curl -H "Authorization: Bearer $GLOBALPING_TOKEN" \
  https://api.globalping.io/v1/limits
```

### 方法 3：使用 jq 格式化輸出

```bash
curl -s -H "Authorization: Bearer gp_uh5vlg4ttg3v5gwby5zgtqrciimahql5" \
  https://api.globalping.io/v1/limits | jq .
```

## 📊 額度資訊說明

### 免費用戶限制

```json
{
  "measurements": {
    "rateLimit": {
      "limit": 100,        // 每分鐘最多 100 次
      "remaining": 95,     // 剩餘次數
      "reset": 1709769600  // 重置時間（Unix 時間戳）
    }
  },
  "credits": {
    "remaining": 9500      // 本月剩餘額度
  }
}
```

### 付費用戶限制

- **每分鐘**: 500-1000 次
- **每月**: 100,000+ 次

## 🧪 測試 API 連線

### 簡單測試

```bash
# 測試單個域名
curl -X POST https://api.globalping.io/v1/measurements \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer gp_uh5vlg4ttg3v5gwby5zgtqrciimahql5" \
  -d '{
    "type": "http",
    "target": "google.com",
    "limit": 1,
    "locations": [{"country": "ID"}]
  }'
```

### 檢查測量結果

```bash
# 替換 MEASUREMENT_ID 為上面返回的 ID
curl -H "Authorization: Bearer gp_uh5vlg4ttg3v5gwby5zgtqrciimahql5" \
  https://api.globalping.io/v1/measurements/MEASUREMENT_ID
```

## 📈 監控額度使用

### 在檢測前檢查額度

```bash
# 檢查剩餘額度
REMAINING=$(curl -s -H "Authorization: Bearer $GLOBALPING_TOKEN" \
  https://api.globalping.io/v1/limits | \
  jq -r '.credits.remaining')

echo "剩餘額度: $REMAINING"

if [ "$REMAINING" -lt 100 ]; then
    echo "⚠️  額度不足，請稍後再試"
    exit 1
fi
```

### 計算所需額度

```bash
# 計算檢測所需額度
DOMAIN_COUNT=$(wc -l < domains.txt)
PROBES_PER_DOMAIN=3
TOTAL_NEEDED=$((DOMAIN_COUNT * PROBES_PER_DOMAIN))

echo "域名數量: $DOMAIN_COUNT"
echo "每個域名探測數: $PROBES_PER_DOMAIN"
echo "總共需要: $TOTAL_NEEDED 次測量"
```

## 💡 優化建議

### 1. 增加檢測間隔

```bash
# 在檢測腳本中
DELAY=10  # 從 8 秒增加到 10 秒
```

### 2. 減少批次大小

```bash
BATCH_SIZE=20  # 從 30 減少到 20
```

### 3. 減少探測節點數

```bash
# 從 3 個節點減少到 2 個
"limit": 2
```

### 4. 分時段檢測

```bash
# 將域名分成多批，分時段檢測
# 早上檢測一半，晚上檢測另一半
```

## 🔧 在 EC2 上檢查額度

```bash
# SSH 到 EC2
ssh ec2-user@54.238.247.106

# 上傳檢查腳本
scp check-api-quota.sh ec2-user@54.238.247.106:~/

# 執行檢查
bash check-api-quota.sh
```

## 📅 定期監控

### 設置每日額度檢查

```bash
# 添加到 crontab
0 0 * * * ~/check-api-quota.sh >> ~/api-quota.log 2>&1
```

## ⚠️ 額度不足時的處理

### 1. 等待重置

```bash
# 查看重置時間
curl -s -H "Authorization: Bearer $GLOBALPING_TOKEN" \
  https://api.globalping.io/v1/limits | \
  jq -r '.measurements.rateLimit.reset'
```

### 2. 升級到付費計劃

訪問：https://www.globalping.io/pricing

### 3. 使用多個 API Token

```bash
# 輪流使用不同的 Token
TOKENS=(
  "token1"
  "token2"
  "token3"
)
```

## 📊 額度使用統計

### 記錄每次檢測的額度使用

```bash
# 在檢測前後記錄額度
BEFORE=$(curl -s -H "Authorization: Bearer $GLOBALPING_TOKEN" \
  https://api.globalping.io/v1/limits | jq -r '.credits.remaining')

# 執行檢測
./id_globalping_multi_v3.3_Telegram.sh domains.txt

AFTER=$(curl -s -H "Authorization: Bearer $GLOBALPING_TOKEN" \
  https://api.globalping.io/v1/limits | jq -r '.credits.remaining')

USED=$((BEFORE - AFTER))
echo "本次使用額度: $USED"
```

---

**快速開始**：執行 `bash check-api-quota.sh` 查看當前額度！
