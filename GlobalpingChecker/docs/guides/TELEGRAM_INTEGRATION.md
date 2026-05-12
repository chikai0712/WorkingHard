# Telegram 通知集成指南

## 🎯 功能說明

為 Globalping Checker 添加 Telegram 通知功能，自動將檢測結果發送到 Telegram。

## ✨ 通知內容

### 1. 檢測開始通知
```
🚀 開始域名檢測

總域名數: 100
開始時間: 2026-03-07 12:30:00
```

### 2. 單個域名結果（可選）
```
🚨 example.com - BLOCKED

BIZNET NETWORKS: 36.86.63.185 - BLOCKED
Media Sarana Data: 36.86.63.185 - BLOCKED
XL Axiata: 36.86.63.185 - BLOCKED
```

### 3. 檢測摘要報告
```
🚨 域名檢測報告

📊 檢測統計
總域名數: 100
檢測時間: 2026-03-07 12:30:00

📈 檢測結果
✅ 正常連通: 85
🚨 DNS 污染: 10
⚠️ 完全超時: 3
⚠️ 服務異常: 1
🔄 部分異常: 1
❌ 檢測失敗: 0
```

## 🚀 快速開始

### 步驟 1：創建 Telegram Bot

1. 在 Telegram 搜尋 **@BotFather**
2. 發送 `/newbot`
3. 按提示設置 Bot 名稱（例如：Globalping Checker Bot）
4. 複製 Bot Token（格式：`123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`）

### 步驟 2：獲取 Chat ID

**方法 1：使用 @userinfobot**
1. 在 Telegram 搜尋 **@userinfobot**
2. 發送任意消息
3. Bot 會回覆你的 Chat ID

**方法 2：手動獲取**
1. 向你的 Bot 發送任意消息
2. 訪問：`https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. 找到 `"chat":{"id":123456789}`

### 步驟 3：配置 Telegram 通知

在**系統終端**執行：

```bash
cd ~/Desktop/Project/GlobalpingChecker
bash setup-telegram.sh
```

按提示輸入：
- Bot Token（必填）
- Chat ID（必填）
- Bot 名稱（可選）

配置完成後會自動發送測試消息。

### 步驟 4：測試通知

```bash
bash id_globalping_multi_v3.3_Telegram.sh test_2_domains.txt
```

檢查 Telegram 是否收到通知。

### 步驟 5：部署到 EC2

```bash
# 上傳配置
scp telegram-config.env ec2-user@YOUR_IP:/tmp/
scp telegram-notify.sh ec2-user@YOUR_IP:/tmp/
scp id_globalping_multi_v3.3_Telegram.sh ec2-user@YOUR_IP:/tmp/

# SSH 到 EC2
ssh ec2-user@YOUR_IP

# 移動文件
sudo mv /tmp/telegram-config.env /opt/globalping-checker/
sudo mv /tmp/telegram-notify.sh /opt/globalping-checker/
sudo mv /tmp/id_globalping_multi_v3.3_Telegram.sh /opt/globalping-checker/
sudo chmod +x /opt/globalping-checker/*.sh

# 測試
/opt/globalping-checker/id_globalping_multi_v3.3_Telegram.sh /opt/globalping-checker/domains.txt
```

## ⚙️ 配置選項

編輯 `telegram-config.env`：

```bash
# Bot Token（必填）
TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

# Chat ID（必填）
TELEGRAM_CHAT_ID="123456789"

# Bot 名稱（可選）
TELEGRAM_BOT_NAME="Globalping Checker"

# 通知級別
# all: 所有檢測都通知
# errors: 只通知錯誤（BLOCKED, TIMEOUT, WARNING, PARTIAL, API_ERROR）
# critical: 只通知嚴重錯誤（BLOCKED, API_ERROR）
TELEGRAM_NOTIFY_LEVEL="errors"

# 是否啟用通知
TELEGRAM_ENABLED="true"

# 是否使用 Markdown 格式
TELEGRAM_USE_MARKDOWN="true"
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

### 發送到群組

1. 將 Bot 添加到群組
2. 在群組中發送消息
3. 訪問 `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. 找到群組的 Chat ID（通常是負數，例如：-123456789）
5. 在配置中使用群組 Chat ID

### 發送到頻道

1. 創建頻道並將 Bot 設為管理員
2. 獲取頻道 ID（格式：`@channel_name` 或 `-100123456789`）
3. 在配置中使用頻道 ID

### 自定義通知格式

編輯 `telegram-notify.sh` 中的函數，可以自定義消息格式。

## 📝 使用示例

### 本地測試

```bash
cd ~/Desktop/Project/GlobalpingChecker

# 配置 Telegram
bash setup-telegram.sh

# 測試通知
bash id_globalping_multi_v3.3_Telegram.sh test_2_domains.txt
```

### EC2 自動通知

```bash
# 更新 EC2 上的 cron 任務
ssh ec2-user@YOUR_IP
crontab -e

# 修改為使用 Telegram 版本
0 2 * * * /opt/globalping-checker/id_globalping_multi_v3.3_Telegram.sh /opt/globalping-checker/domains.txt
```

## 🐛 故障排除

### 問題 1：測試消息未收到

**檢查**：
```bash
# 測試 Bot Token
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"
```

**解決**：
- 確認 Bot Token 正確
- 確認已向 Bot 發送過消息
- 檢查 Chat ID 是否正確

### 問題 2：通知未發送

**檢查**：
```bash
# 查看配置
cat telegram-config.env

# 檢查 TELEGRAM_ENABLED
grep TELEGRAM_ENABLED telegram-config.env
```

**解決**：
- 確認 `TELEGRAM_ENABLED="true"`
- 檢查配置文件路徑
- 查看腳本日誌

### 問題 3：通知太多

**解決**：
```bash
# 修改通知級別
nano telegram-config.env

# 改為
TELEGRAM_NOTIFY_LEVEL="critical"
```

### 問題 4：群組無法接收

**解決**：
- 確認 Bot 已加入群組
- 確認 Bot 有發送消息權限
- 使用正確的群組 Chat ID（負數）

## 💡 Telegram vs Slack

| 特性 | Telegram | Slack |
|------|----------|-------|
| **設置難度** | 簡單 | 中等 |
| **免費額度** | 無限制 | 有限制 |
| **消息格式** | Markdown | Blocks API |
| **適用場景** | 個人/小團隊 | 企業團隊 |
| **通知速度** | 快 | 快 |

## 📚 相關文件

- `setup-telegram.sh` - Telegram 配置腳本
- `telegram-notify.sh` - Telegram 通知函數庫
- `id_globalping_multi_v3.3_Telegram.sh` - 支持 Telegram 的檢測腳本
- `telegram-config.env` - Telegram 配置文件

## 🎯 最佳實踐

1. **使用 errors 級別**：避免通知過多
2. **定期檢查**：確認通知正常工作
3. **備份配置**：保存 Bot Token 和 Chat ID
4. **測試先行**：先用少量域名測試
5. **群組通知**：團隊協作使用群組

---

**創建時間**: 2026-03-07  
**版本**: 1.0.0
