# Slack 通知集成指南

## 🎯 功能說明

為 Globalping Checker 添加 Slack 通知功能，自動將檢測結果發送到 Slack 頻道。

## ✨ 通知內容

### 1. 檢測開始通知
```
🚀 開始檢測 100 個域名...
```

### 2. 單個域名結果（可選）
```
🚨 example.com - BLOCKED
  - BIZNET NETWORKS: 36.86.63.185 - BLOCKED
  - Media Sarana Data: 36.86.63.185 - BLOCKED
  - XL Axiata: 36.86.63.185 - BLOCKED
```

### 3. 檢測摘要報告
```
🔍 域名檢測報告

總域名數: 100
檢測時間: 2026-03-07 12:30:00

✅ 正常連通: 85
🚨 DNS 污染: 10
⚠️ 完全超時: 3
⚠️ 服務異常: 1
🔄 部分異常: 1
❌ 檢測失敗: 0
```

## 🚀 快速開始

### 步驟 1：獲取 Slack Webhook URL

1. 訪問 https://api.slack.com/apps
2. 點擊 "Create New App" → "From scratch"
3. 輸入應用名稱（例如：Globalping Checker）
4. 選擇工作區
5. 在左側菜單選擇 "Incoming Webhooks"
6. 啟用 "Activate Incoming Webhooks"
7. 點擊 "Add New Webhook to Workspace"
8. 選擇要發送通知的頻道
9. 複製 Webhook URL（格式：`https://hooks.slack.com/services/...`）

### 步驟 2：配置 Slack 通知

```bash
cd ~/Desktop/Project/AWS-deploy
./setup-slack.sh
```

按提示輸入：
- Slack Webhook URL（必填）
- 頻道名稱（可選，例如：#monitoring）
- 機器人名稱（可選，例如：Globalping Bot）

配置完成後會自動發送測試消息。

### 步驟 3：上傳配置到 EC2

```bash
# 方法 1：手動上傳
scp slack-config.env ec2-user@YOUR_IP:/tmp/
ssh ec2-user@YOUR_IP 'sudo mv /tmp/slack-config.env /opt/globalping-checker/'

scp ~/Desktop/Project/GlobalpingChecker/slack-notify.sh ec2-user@YOUR_IP:/tmp/
ssh ec2-user@YOUR_IP 'sudo mv /tmp/slack-notify.sh /opt/globalping-checker/'

scp ~/Desktop/Project/GlobalpingChecker/id_globalping_multi_v3.2_Slack.sh ec2-user@YOUR_IP:/tmp/
ssh ec2-user@YOUR_IP 'sudo mv /tmp/id_globalping_multi_v3.2_Slack.sh /opt/globalping-checker/ && sudo chmod +x /opt/globalping-checker/id_globalping_multi_v3.2_Slack.sh'

# 方法 2：使用更新腳本（推薦）
cd ~/Desktop/Project/AWS-deploy
./update-globalping-with-slack.sh
```

### 步驟 4：測試通知

```bash
# SSH 到 EC2
ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@YOUR_IP

# 執行測試
cd /opt/globalping-checker
./id_globalping_multi_v3.2_Slack.sh test_2_domains.txt
```

## ⚙️ 配置選項

編輯 `slack-config.env`：

```bash
# Webhook URL（必填）
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# 頻道名稱（可選）
SLACK_CHANNEL="#monitoring"

# 機器人名稱（可選）
SLACK_BOT_NAME="Globalping Checker"

# 通知級別
# all: 所有檢測都通知
# errors: 只通知錯誤（BLOCKED, TIMEOUT, WARNING, PARTIAL, API_ERROR）
# critical: 只通知嚴重錯誤（BLOCKED, API_ERROR）
SLACK_NOTIFY_LEVEL="errors"

# 是否啟用通知
SLACK_ENABLED="true"
```

## 📊 通知級別說明

### all（全部通知）
- 每個域名的檢測結果都會發送
- 適合：測試階段、小量域名

### errors（錯誤通知）- 推薦
- 只通知有問題的域名
- 包括：BLOCKED、TIMEOUT、WARNING、PARTIAL、API_ERROR
- 適合：生產環境、大量域名

### critical（嚴重錯誤）
- 只通知最嚴重的問題
- 包括：BLOCKED、API_ERROR
- 適合：只關注 DNS 污染和 API 錯誤

## 🔧 進階使用

### 自定義通知格式

編輯 `slack-notify.sh` 中的 `send_slack_summary` 函數。

### 添加 @mention

在配置中添加：
```bash
SLACK_MENTION="<!channel>"  # 通知所有人
# 或
SLACK_MENTION="<@USER_ID>"  # 通知特定用戶
```

### 多頻道通知

創建多個配置文件：
```bash
slack-config-monitoring.env  # 監控頻道
slack-config-alerts.env      # 告警頻道
```

## 📝 使用示例

### 本地測試

```bash
cd ~/Desktop/Project/GlobalpingChecker

# 配置 Slack
cd ../AWS-deploy
./setup-slack.sh

# 測試通知
cd ~/Desktop/Project/GlobalpingChecker
./id_globalping_multi_v3.2_Slack.sh test_2_domains.txt
```

### EC2 自動通知

```bash
# 更新 EC2 上的 cron 任務
ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@YOUR_IP

# 編輯 crontab
crontab -e

# 修改為使用 Slack 版本
0 2 * * * /opt/globalping-checker/id_globalping_multi_v3.2_Slack.sh /opt/globalping-checker/domains.txt
```

## 🐛 故障排除

### 問題 1：測試消息未收到

**檢查**：
```bash
# 測試 Webhook URL
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"測試"}' \
  YOUR_WEBHOOK_URL
```

**解決**：
- 確認 Webhook URL 正確
- 檢查 Slack 應用權限
- 確認頻道存在

### 問題 2：通知未發送

**檢查**：
```bash
# 查看配置
cat /opt/globalping-checker/slack-config.env

# 檢查 SLACK_ENABLED
grep SLACK_ENABLED /opt/globalping-checker/slack-config.env
```

**解決**：
- 確認 `SLACK_ENABLED="true"`
- 檢查配置文件路徑
- 查看腳本日誌

### 問題 3：通知太多

**解決**：
```bash
# 修改通知級別
nano /opt/globalping-checker/slack-config.env

# 改為
SLACK_NOTIFY_LEVEL="critical"
```

## 📚 相關文件

- `setup-slack.sh` - Slack 配置腳本
- `slack-notify.sh` - Slack 通知函數庫
- `id_globalping_multi_v3.2_Slack.sh` - 支持 Slack 的檢測腳本
- `slack-config.env` - Slack 配置文件

## 💡 最佳實踐

1. **使用 errors 級別**：避免通知過多
2. **定期檢查**：確認通知正常工作
3. **備份配置**：保存 Webhook URL
4. **測試先行**：先用少量域名測試
5. **監控頻道**：創建專門的監控頻道

---

**創建時間**: 2026-03-07  
**版本**: 1.0.0
