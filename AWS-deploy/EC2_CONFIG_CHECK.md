# 查看 EC2 上的檢測腳本配置

## 🔍 在系統終端執行以下命令

### 1. 查看 smart-check.sh 配置

```bash
ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@54.238.247.106 'grep -E "API_TOKEN|QUOTA_THRESHOLD|DOMAINS_FILE" ~/globalping-checker/smart-check.sh | head -5'
```

**預期輸出**：
```bash
API_TOKEN="uh5vlg4ttg3v5gwby5zgtqrciimahql5"
QUOTA_THRESHOLD=300
DOMAINS_FILE="${1:-domains.txt}"
```

### 2. 查看 auto-quota-check.sh 配置

```bash
ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@54.238.247.106 'grep -E "API_TOKEN|QUOTA_THRESHOLD|CHECK_INTERVAL" ~/globalping-checker/auto-quota-check.sh | head -5'
```

**預期輸出**：
```bash
API_TOKEN="uh5vlg4ttg3v5gwby5zgtqrciimahql5"
QUOTA_THRESHOLD=300
CHECK_INTERVAL=600  # 10 分鐘
```

### 3. 查看 Telegram 配置

```bash
ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@54.238.247.106 'cat ~/globalping-checker/telegram-config.env'
```

**預期輸出**：
```bash
TELEGRAM_BOT_TOKEN="8771241397:AAESXT-Cn5EQ6sRBiHar1AKKwiQPKxJ_dJo"
TELEGRAM_CHAT_ID="229891358"
TELEGRAM_BOT_NAME="DNS 檢測機器人"
TELEGRAM_NOTIFY_LEVEL="errors"
TELEGRAM_ENABLED="true"
TELEGRAM_USE_MARKDOWN="true"
```

### 4. 查看 Crontab 定時任務

```bash
ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@54.238.247.106 'crontab -l'
```

**預期輸出**：
```bash
*/10 * * * * cd ~/globalping-checker && bash smart-check.sh domains.txt >> ~/smart-check.log 2>&1
```

### 5. 查看所有文件

```bash
ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@54.238.247.106 'ls -lh ~/globalping-checker/'
```

**預期輸出**：
```bash
-rwxr-xr-x. 1 ec2-user ec2-user 3.6K Mar  7 01:27 auto-quota-check.sh
-rwxr-xr-x. 1 ec2-user ec2-user 9.0K Mar  7 01:27 id_globalping_multi_v3.3_Telegram.sh
-rwxr-xr-x. 1 ec2-user ec2-user 2.3K Mar  7 01:27 smart-check.sh
-rw-r--r--. 1 ec2-user ec2-user  553 Mar  7 01:27 telegram-config.env
-rwxr-xr-x. 1 ec2-user ec2-user 4.8K Mar  7 01:27 telegram-notify.sh
-rw-r--r--. 1 ec2-user ec2-user   24 Mar  6 17:05 test_domains.txt
```

### 6. 查看完整的 smart-check.sh 腳本

```bash
ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@54.238.247.106 'cat ~/globalping-checker/smart-check.sh'
```

## 📊 當前配置總結

根據最新部署，EC2 上的配置應該是：

### 檢測腳本配置
- **API Token**: `uh5vlg4ttg3v5gwby5zgtqrciimahql5`
- **額度閾值**: `300`（額度 >= 300 才執行）
- **檢查間隔**: 每 10 分鐘
- **域名文件**: `domains.txt`

### Telegram 配置
- **Bot Token**: `8771241397:AAESXT-Cn5EQ6sRBiHar1AKKwiQPKxJ_dJo`
- **Chat ID**: `229891358`
- **Bot 名稱**: DNS 檢測機器人
- **通知級別**: errors（只通知錯誤）
- **狀態**: 已啟用

### Cron 定時任務
- **執行頻率**: 每 10 分鐘（:00, :10, :20, :30, :40, :50）
- **執行命令**: `cd ~/globalping-checker && bash smart-check.sh domains.txt`
- **日誌位置**: `~/smart-check.log`

### 工作流程
```
每 10 分鐘
    ↓
檢查 API 額度
    ↓
額度 >= 300？
    ↓ 是
執行域名檢測（100 域名 × 3 探測器）
    ↓
發送 Telegram 通知
    ↓
記錄日誌
```

## 🔧 快速檢查命令

```bash
# 一次查看所有關鍵配置
ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@54.238.247.106 << 'EOF'
echo "=== 配置摘要 ==="
echo ""
echo "1. 額度閾值:"
grep QUOTA_THRESHOLD ~/globalping-checker/smart-check.sh | head -1
echo ""
echo "2. API Token:"
grep API_TOKEN ~/globalping-checker/smart-check.sh | head -1
echo ""
echo "3. Crontab:"
crontab -l
echo ""
echo "4. Telegram 狀態:"
grep TELEGRAM_ENABLED ~/globalping-checker/telegram-config.env
EOF
```

---

**在系統終端執行上述命令查看 EC2 上的完整配置！**
