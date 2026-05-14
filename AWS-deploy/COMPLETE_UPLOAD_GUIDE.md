# 🚀 完整部署指南 - 在系統終端執行

## ⚠️ 重要：必須在系統終端執行

所有 AWS 和 SSH 操作都必須在系統終端（Terminal.app）執行，不能在 Cursor 中執行。

## 🎯 一鍵部署

### 在系統終端執行：

```bash
cd ~/Desktop/Project/AWS-deploy
bash complete-upload.sh
```

這個腳本會自動：
1. ✅ 查詢實例使用的密鑰
2. ✅ 測試 SSH 連線
3. ✅ 上傳所有文件
4. ✅ 配置 EC2 環境
5. ✅ 提供 cron 設置指令
6. ✅ 可選：執行測試

## 📝 手動部署步驟

如果自動腳本失敗，可以手動執行：

### 步驟 1：查詢密鑰名稱

```bash
aws ec2 describe-instances \
  --region ap-northeast-1 \
  --instance-ids i-064d5f817958cf68e \
  --query 'Reservations[0].Instances[0].KeyName' \
  --output text
```

### 步驟 2：測試 SSH

```bash
# 替換 YOUR_KEY_NAME
ssh -i ~/.ssh/YOUR_KEY_NAME.pem ec2-user@54.238.247.106
```

### 步驟 3：上傳文件

```bash
cd ~/Desktop/Project/GlobalpingChecker

# 上傳所有文件
scp -i ~/.ssh/YOUR_KEY_NAME.pem smart-check.sh ec2-user@54.238.247.106:~/
scp -i ~/.ssh/YOUR_KEY_NAME.pem auto-quota-check.sh ec2-user@54.238.247.106:~/
scp -i ~/.ssh/YOUR_KEY_NAME.pem telegram-config.env ec2-user@54.238.247.106:~/
scp -i ~/.ssh/YOUR_KEY_NAME.pem telegram-notify.sh ec2-user@54.238.247.106:~/
scp -i ~/.ssh/YOUR_KEY_NAME.pem id_globalping_multi_v3.3_Telegram.sh ec2-user@54.238.247.106:~/
```

### 步驟 4：配置 EC2

```bash
ssh -i ~/.ssh/YOUR_KEY_NAME.pem ec2-user@54.238.247.106

# 創建目錄
mkdir -p ~/globalping-checker

# 移動文件
mv ~/*.sh ~/globalping-checker/
mv ~/telegram-*.* ~/globalping-checker/

# 設置權限
cd ~/globalping-checker
chmod +x *.sh

# 測試
bash smart-check.sh domains.txt
```

### 步驟 5：設置定時任務

```bash
# 在 EC2 上
crontab -e
```

添加：
```bash
# 每 10 分鐘檢查額度並智能執行
*/10 * * * * cd ~/globalping-checker && bash smart-check.sh domains.txt >> ~/smart-check.log 2>&1
```

## 🔍 故障排除

### 問題 1：找不到密鑰

**解決**：
```bash
# 列出所有密鑰
ls -la ~/.ssh/*.pem

# 從 AWS 查詢
aws ec2 describe-instances \
  --region ap-northeast-1 \
  --instance-ids i-064d5f817958cf68e \
  --query 'Reservations[0].Instances[0].KeyName'
```

### 問題 2：SSH 連線失敗

**檢查**：
1. 實例是否正在運行
2. 安全組是否允許你的 IP
3. 密鑰權限是否正確

**修復**：
```bash
# 修正密鑰權限
chmod 400 ~/.ssh/*.pem

# 檢查安全組
aws ec2 describe-security-groups \
  --region ap-northeast-1 \
  --filters "Name=group-name,Values=*globalping*"
```

### 問題 3：上傳失敗

**解決**：
```bash
# 確認文件存在
ls -la ~/Desktop/Project/GlobalpingChecker/*.sh

# 使用詳細模式上傳
scp -v -i ~/.ssh/YOUR_KEY.pem file.sh ec2-user@54.238.247.106:~/
```

## 📊 驗證部署

### 檢查文件

```bash
ssh -i ~/.ssh/YOUR_KEY.pem ec2-user@54.238.247.106 \
  'ls -la ~/globalping-checker/'
```

### 測試檢測

```bash
ssh -i ~/.ssh/YOUR_KEY.pem ec2-user@54.238.247.106 \
  'cd ~/globalping-checker && bash smart-check.sh domains.txt'
```

### 查看日誌

```bash
ssh -i ~/.ssh/YOUR_KEY.pem ec2-user@54.238.247.106 \
  'tail -f ~/smart-check.log'
```

## 🎯 快速命令參考

```bash
# 查詢實例資訊
aws ec2 describe-instances --region ap-northeast-1 --instance-ids i-064d5f817958cf68e

# SSH 連線
ssh -i ~/.ssh/YOUR_KEY.pem ec2-user@54.238.247.106

# 上傳文件
scp -i ~/.ssh/YOUR_KEY.pem file.sh ec2-user@54.238.247.106:~/

# 執行檢測
ssh -i ~/.ssh/YOUR_KEY.pem ec2-user@54.238.247.106 'cd ~/globalping-checker && bash smart-check.sh domains.txt'

# 查看日誌
ssh -i ~/.ssh/YOUR_KEY.pem ec2-user@54.238.247.106 'tail -50 ~/smart-check.log'
```

---

**現在在系統終端執行 `bash complete-upload.sh` 開始部署！** 🚀
