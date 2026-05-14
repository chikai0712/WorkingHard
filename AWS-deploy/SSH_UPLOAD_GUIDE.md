# SSH 連線和文件上傳指南

## 🔑 找到正確的 SSH 密鑰

### 查看可用的密鑰

```bash
ls -la ~/.ssh/*.pem
```

### 從 AWS 控制台查看

根據你的截圖，實例使用的 Key 名稱可以在 EC2 控制台看到。

## 📤 上傳文件的正確命令

### 使用正確的密鑰上傳

```bash
# 格式：scp -i <密鑰路徑> <本地文件> ec2-user@<IP>:<遠端路徑>

# 上傳 smart-check.sh
scp -i ~/.ssh/YOUR_KEY_NAME.pem smart-check.sh ec2-user@54.238.247.106:~/

# 上傳 auto-quota-check.sh
scp -i ~/.ssh/YOUR_KEY_NAME.pem auto-quota-check.sh ec2-user@54.238.247.106:~/

# 上傳 Telegram 配置
scp -i ~/.ssh/YOUR_KEY_NAME.pem telegram-config.env ec2-user@54.238.247.106:~/
scp -i ~/.ssh/YOUR_KEY_NAME.pem telegram-notify.sh ec2-user@54.238.247.106:~/
scp -i ~/.ssh/YOUR_KEY_NAME.pem id_globalping_multi_v3.3_Telegram.sh ec2-user@54.238.247.106:~/
```

## 🔍 常見的密鑰名稱

根據之前的部署腳本，可能的密鑰名稱：
- `globalping-checker-key.pem`
- `globalping-v4-key.pem`
- `tokyo-key.pem`
- `aws-key.pem`

## 🧪 測試 SSH 連線

```bash
# 測試連線（替換 YOUR_KEY_NAME）
ssh -i ~/.ssh/YOUR_KEY_NAME.pem ec2-user@54.238.247.106

# 如果成功，你會看到 EC2 的歡迎訊息
```

## 📋 完整上傳流程

### 步驟 1：找到密鑰

```bash
ls ~/.ssh/*.pem
```

### 步驟 2：測試連線

```bash
ssh -i ~/.ssh/YOUR_KEY_NAME.pem ec2-user@54.238.247.106
```

### 步驟 3：上傳所有文件

```bash
cd ~/Desktop/Project/GlobalpingChecker

# 上傳智能檢測腳本
scp -i ~/.ssh/YOUR_KEY_NAME.pem smart-check.sh ec2-user@54.238.247.106:~/
scp -i ~/.ssh/YOUR_KEY_NAME.pem auto-quota-check.sh ec2-user@54.238.247.106:~/

# 上傳 Telegram 相關文件
scp -i ~/.ssh/YOUR_KEY_NAME.pem telegram-config.env ec2-user@54.238.247.106:~/
scp -i ~/.ssh/YOUR_KEY_NAME.pem telegram-notify.sh ec2-user@54.238.247.106:~/
scp -i ~/.ssh/YOUR_KEY_NAME.pem id_globalping_multi_v3.3_Telegram.sh ec2-user@54.238.247.106:~/
```

### 步驟 4：SSH 到 EC2 並配置

```bash
ssh -i ~/.ssh/YOUR_KEY_NAME.pem ec2-user@54.238.247.106

# 創建目錄（如果不存在）
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

## 🔧 如果找不到密鑰

### 從 AWS 控制台下載

1. 登入 AWS 控制台
2. 進入 EC2 → Key Pairs
3. 如果密鑰遺失，需要：
   - 創建新密鑰對
   - 停止實例
   - 分離根卷
   - 掛載到另一個實例
   - 添加新公鑰到 `~/.ssh/authorized_keys`
   - 重新掛載並啟動

### 或使用 AWS Systems Manager Session Manager

如果實例有 SSM 權限：

```bash
aws ssm start-session --target i-064d5f817958cf68e --region ap-northeast-1
```

## 💡 快速解決方案

### 使用部署腳本（推薦）

```bash
cd ~/Desktop/Project/AWS-deploy
./deploy-to-existing-ec2.sh
```

這個腳本會自動：
1. 找到正確的密鑰
2. 測試連線
3. 上傳所有文件
4. 配置環境

---

**請先執行 `ls ~/.ssh/*.pem` 找到密鑰名稱！**
