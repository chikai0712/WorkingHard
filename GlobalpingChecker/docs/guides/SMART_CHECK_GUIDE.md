# 智能額度監控和自動檢測指南

## 🤖 功能說明

創建了兩個智能檢測腳本：

### 1. auto-quota-check.sh - 持續監控版本
- 每 10 分鐘自動檢查額度
- 當額度 >= 400 時自動執行檢測
- 持續運行，適合後台服務

### 2. smart-check.sh - 單次檢測版本
- 檢查一次額度
- 如果 >= 400 則執行檢測
- 適合 cron 定時任務

## 🚀 使用方式

### 方法 1：持續監控（推薦用於開發/測試）

```bash
cd ~/Desktop/Project/GlobalpingChecker
bash auto-quota-check.sh domains.txt
```

**特點**：
- 持續運行，每 10 分鐘檢查一次
- 自動執行檢測
- 記錄日誌到 `auto-check.log`
- 按 `Ctrl+C` 停止

### 方法 2：單次智能檢測（推薦用於 cron）

```bash
bash smart-check.sh domains.txt
```

**特點**：
- 檢查一次額度
- 額度足夠才執行
- 適合定時任務

## 📅 設置定時任務

### 在本地設置（每 10 分鐘檢查）

```bash
crontab -e
```

添加：
```bash
# 每 10 分鐘檢查額度並智能執行
*/10 * * * * cd ~/Desktop/Project/GlobalpingChecker && bash smart-check.sh domains.txt >> ~/globalping-cron.log 2>&1
```

### 在 EC2 上設置

```bash
# SSH 到 EC2
ssh ec2-user@54.238.247.106

# 編輯 crontab
crontab -e
```

添加：
```bash
# 每 10 分鐘檢查額度並智能執行
*/10 * * * * cd ~/globalping-checker && bash smart-check.sh domains.txt >> ~/smart-check.log 2>&1
```

## ⚙️ 配置參數

### 修改額度閾值

編輯腳本中的 `QUOTA_THRESHOLD`：

```bash
# 默認 400
QUOTA_THRESHOLD=400

# 可以改為其他值，例如：
QUOTA_THRESHOLD=300  # 更激進，額度 >= 300 就執行
QUOTA_THRESHOLD=450  # 更保守，額度 >= 450 才執行
```

### 修改檢查間隔

編輯 `auto-quota-check.sh` 中的 `CHECK_INTERVAL`：

```bash
# 默認 600 秒（10 分鐘）
CHECK_INTERVAL=600

# 可以改為：
CHECK_INTERVAL=300   # 5 分鐘
CHECK_INTERVAL=900   # 15 分鐘
CHECK_INTERVAL=1800  # 30 分鐘
```

## 📊 日誌查看

### 持續監控版本

```bash
# 查看實時日誌
tail -f ~/Desktop/Project/GlobalpingChecker/auto-check.log

# 查看最近的日誌
tail -50 ~/Desktop/Project/GlobalpingChecker/auto-check.log
```

### 單次檢測版本（cron）

```bash
# 查看 cron 日誌
tail -f ~/globalping-cron.log
```

## 📝 日誌示例

```
[2026-03-07 01:30:00] ========================================
[2026-03-07 01:30:00] 🤖 智能額度監控啟動
[2026-03-07 01:30:00] ========================================
[2026-03-07 01:30:00] 配置：
[2026-03-07 01:30:00]   API Token: uh5vlg4ttg3v5gwby5z...
[2026-03-07 01:30:00]   額度閾值: 400
[2026-03-07 01:30:00]   檢查間隔: 600 秒 (10 分鐘)
[2026-03-07 01:30:00] ========================================
[2026-03-07 01:30:00] 
[2026-03-07 01:30:00] 🔍 檢查 API 額度...
[2026-03-07 01:30:01] 📊 當前剩餘額度: 404 / 500
[2026-03-07 01:30:01] ✅ 額度充足 (404 >= 400)，開始檢測
[2026-03-07 01:30:01] 🚀 開始執行域名檢測...
[2026-03-07 01:35:23] ✅ 檢測完成
[2026-03-07 01:35:24] 📊 檢測後剩餘額度: 354 / 500
[2026-03-07 01:35:24] ⏰ 等待 10 分鐘後再次檢查...
```

## 🔧 部署到 EC2

### 上傳腳本

```bash
scp auto-quota-check.sh ec2-user@54.238.247.106:~/globalping-checker/
scp smart-check.sh ec2-user@54.238.247.106:~/globalping-checker/
```

### 設置權限

```bash
ssh ec2-user@54.238.247.106
cd ~/globalping-checker
chmod +x auto-quota-check.sh smart-check.sh
```

### 測試運行

```bash
# 測試單次檢測
bash smart-check.sh domains.txt

# 測試持續監控（按 Ctrl+C 停止）
bash auto-quota-check.sh domains.txt
```

### 設置為後台服務（可選）

```bash
# 使用 nohup 在後台運行
nohup bash auto-quota-check.sh domains.txt > auto-check.log 2>&1 &

# 查看進程
ps aux | grep auto-quota-check

# 停止進程
kill <PID>
```

## 💡 使用建議

### 開發/測試階段
使用 `auto-quota-check.sh` 持續監控，方便觀察行為。

### 生產環境
使用 `smart-check.sh` + cron，更穩定可靠。

### 額度管理
- 閾值設為 400 可以確保有足夠額度完成檢測
- 每 10 分鐘檢查一次，平衡了及時性和資源消耗
- 額度每分鐘重置，所以很快就能恢復

## 🎯 優勢

1. **智能判斷**：只在額度充足時執行
2. **自動化**：無需手動干預
3. **節省額度**：避免額度不足時的失敗嘗試
4. **Telegram 通知**：檢測完成自動發送通知
5. **日誌記錄**：完整的執行記錄

---

**現在可以開始使用智能檢測了！** 🚀
