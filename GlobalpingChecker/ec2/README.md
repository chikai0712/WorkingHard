# Globalping Checker - EC2 部署指南

## 📋 架構說明

EC2 部署方案提供完整的控制和靈活性：

- **EC2 Instance**: t3.micro (免費方案)
- **VPC**: 獨立網路環境
- **Elastic IP**: 固定公網 IP
- **Security Group**: SSH 訪問控制
- **IAM Role**: S3 和 SES 權限
- **Cron**: 定時執行檢測

## 🚀 快速部署

### 前置需求

1. **AWS CLI** 已安裝並配置
2. **SSH Key Pair** 已創建

```bash
# 創建 SSH Key Pair (如果還沒有)
aws ec2 create-key-pair \
  --key-name globalping-checker \
  --query 'KeyMaterial' \
  --output text > globalping-checker.pem

chmod 400 globalping-checker.pem
```

### 一鍵部署

```bash
cd ~/Desktop/Project/GlobalpingChecker/ec2
chmod +x deploy-ec2.sh
./deploy-ec2.sh
```

部署腳本會詢問：
- SSH Key Pair 名稱
- 實例類型 (預設: t3.micro)
- SSH 訪問來源 IP
- Globalping API Token (可選)
- S3 Bucket 名稱 (可選)

## 📝 安裝步驟

### 1. 連線到 EC2

```bash
# 使用部署腳本生成的快速連線腳本
./connect.sh

# 或手動連線
ssh -i globalping-checker.pem ec2-user@YOUR_PUBLIC_IP
```

### 2. 上傳項目文件

```bash
# 在本地執行
scp -i globalping-checker.pem -r ~/Desktop/Project/GlobalpingChecker ec2-user@YOUR_PUBLIC_IP:~/
```

### 3. 執行安裝腳本

```bash
# 在 EC2 上執行
cd ~/GlobalpingChecker/ec2
chmod +x setup.sh
./setup.sh
```

安裝腳本會自動：
- 安裝系統依賴 (Python, curl, jq)
- 安裝 Python 套件 (requests, boto3)
- 創建工作目錄 `/opt/globalping-checker`
- 創建日誌目錄 `/var/log/globalping-checker`
- 生成配置文件和執行腳本
- 設置定時任務 (可選)

### 4. 配置系統

```bash
# 編輯配置文件
sudo nano /opt/globalping-checker/config.env
```

配置項目：
```bash
# Globalping API Token (可選)
GLOBALPING_TOKEN="your_token_here"

# 域名文件路徑
DOMAINS_FILE="/opt/globalping-checker/domains.txt"

# 日誌目錄
LOG_DIR="/var/log/globalping-checker"

# S3 Bucket (可選，用於備份結果)
S3_BUCKET="your-bucket-name"

# 通知 Email (可選)
NOTIFICATION_EMAIL="your@email.com"

# 執行排程 (cron 格式)
CRON_SCHEDULE="0 2 * * *"
```

### 5. 上傳域名列表

```bash
# 方法 1: 直接編輯
sudo nano /opt/globalping-checker/domains.txt

# 方法 2: 從本地上傳
scp -i globalping-checker.pem domains.txt ec2-user@YOUR_PUBLIC_IP:/tmp/
sudo mv /tmp/domains.txt /opt/globalping-checker/domains.txt
```

### 6. 執行測試

```bash
# 手動執行一次
/opt/globalping-checker/run_check.sh

# 查看日誌
tail -f /var/log/globalping-checker/check_*.log
```

## ⚙️ 定時任務設置

### 查看當前定時任務

```bash
crontab -l
```

### 編輯定時任務

```bash
crontab -e
```

常用排程：
```bash
# 每天凌晨 2 點
0 2 * * * /opt/globalping-checker/run_check.sh

# 每 6 小時一次
0 */6 * * * /opt/globalping-checker/run_check.sh

# 每週一凌晨 2 點
0 2 * * 1 /opt/globalping-checker/run_check.sh

# 每天早上 8 點和晚上 8 點
0 8,20 * * * /opt/globalping-checker/run_check.sh
```

### 查看 Cron 日誌

```bash
# Amazon Linux 2
sudo tail -f /var/log/cron

# Ubuntu
sudo tail -f /var/log/syslog | grep CRON
```

## 📊 監控與管理

### 查看執行日誌

```bash
# 查看最新日誌
ls -lt /var/log/globalping-checker/

# 實時查看
tail -f /var/log/globalping-checker/check_*.log

# 查看特定日期的日誌
ls /var/log/globalping-checker/check_20260306_*.log
```

### 查看系統資源

```bash
# CPU 和記憶體使用
top

# 磁碟使用
df -h

# 網路連線
netstat -an | grep ESTABLISHED
```

### 查看 Globalping 日誌

```bash
# 查看最新的 globalping 日誌
ls -lt ~/globalping_*.log | head -5

# 查看內容
tail -100 ~/globalping_*.log
```

## 🔧 常用操作

### 手動執行檢測

```bash
/opt/globalping-checker/run_check.sh
```

### 更新域名列表

```bash
sudo nano /opt/globalping-checker/domains.txt
```

### 更新配置

```bash
sudo nano /opt/globalping-checker/config.env
```

### 更新腳本

```bash
# 從本地上傳新版本
scp -i globalping-checker.pem id_globalping_multi_v3.1_Token.sh ec2-user@YOUR_PUBLIC_IP:/tmp/
sudo mv /tmp/id_globalping_multi_v3.1_Token.sh /opt/globalping-checker/
sudo chmod +x /opt/globalping-checker/id_globalping_multi_v3.1_Token.sh
```

### 暫停定時任務

```bash
# 註釋掉 cron 任務
crontab -e
# 在行首添加 # 註釋

# 或直接移除
crontab -r
```

### 重啟 EC2

```bash
# 在 EC2 上執行
sudo reboot

# 或從本地執行
aws ec2 reboot-instances --instance-ids i-xxxxx --region ap-northeast-1
```

### 停止 EC2

```bash
# 停止實例 (保留數據，停止計費)
aws ec2 stop-instances --instance-ids i-xxxxx --region ap-northeast-1

# 啟動實例
aws ec2 start-instances --instance-ids i-xxxxx --region ap-northeast-1
```

## 💾 備份與恢復

### 備份到 S3

```bash
# 手動備份日誌
aws s3 sync /var/log/globalping-checker/ s3://your-bucket/logs/

# 備份配置
aws s3 cp /opt/globalping-checker/config.env s3://your-bucket/config/

# 備份域名列表
aws s3 cp /opt/globalping-checker/domains.txt s3://your-bucket/config/
```

### 自動備份腳本

```bash
# 創建備份腳本
sudo nano /opt/globalping-checker/backup.sh
```

```bash
#!/bin/bash
S3_BUCKET="your-bucket-name"
DATE=$(date +%Y%m%d)

# 備份日誌
aws s3 sync /var/log/globalping-checker/ s3://$S3_BUCKET/backups/$DATE/logs/

# 備份配置
aws s3 cp /opt/globalping-checker/config.env s3://$S3_BUCKET/backups/$DATE/config/

echo "備份完成: $DATE"
```

```bash
# 設置權限
sudo chmod +x /opt/globalping-checker/backup.sh

# 添加到 cron (每週日凌晨 3 點)
crontab -e
# 添加: 0 3 * * 0 /opt/globalping-checker/backup.sh
```

## 💰 成本估算

### t3.micro 實例 (免費方案)

| 項目 | 用量 | 月成本 (USD) |
|------|------|-------------|
| EC2 t3.micro | 750 小時/月 | $0.00 (免費額度) |
| EBS 20GB | 20 GB | $0.00 (免費額度 30GB) |
| 數據傳輸 | ~1 GB/月 | $0.00 (免費額度 15GB) |
| Elastic IP | 綁定到運行實例 | $0.00 |
| **總計** | | **$0.00/月** |

### 超過免費額度後

| 項目 | 用量 | 月成本 (USD) |
|------|------|-------------|
| EC2 t3.micro | 24/7 運行 | ~$7.50 |
| EBS 20GB | 20 GB | ~$2.00 |
| 數據傳輸 | ~1 GB/月 | ~$0.09 |
| **總計** | | **~$9.59/月** |

## 🔒 安全性建議

### 1. 限制 SSH 訪問

```bash
# 只允許特定 IP 訪問
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 22 \
  --cidr YOUR_IP/32
```

### 2. 定期更新系統

```bash
# Amazon Linux 2
sudo yum update -y

# Ubuntu
sudo apt-get update && sudo apt-get upgrade -y
```

### 3. 設置防火牆

```bash
# 安裝 firewalld (Amazon Linux 2)
sudo yum install -y firewalld
sudo systemctl start firewalld
sudo systemctl enable firewalld

# 只允許 SSH
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

### 4. 使用 IAM Role

不要在配置文件中存儲 AWS 憑證，使用 IAM Role。

### 5. 加密敏感配置

```bash
# 使用 AWS Secrets Manager
aws secretsmanager create-secret \
  --name globalping-token \
  --secret-string "your_token_here"

# 在腳本中讀取
TOKEN=$(aws secretsmanager get-secret-value \
  --secret-id globalping-token \
  --query SecretString \
  --output text)
```

## 🔍 故障排除

### 問題 1: SSH 連線失敗

**檢查**:
```bash
# 檢查實例狀態
aws ec2 describe-instances --instance-ids i-xxxxx

# 檢查安全組規則
aws ec2 describe-security-groups --group-ids sg-xxxxx
```

**解決**:
- 確認 Key Pair 權限: `chmod 400 key.pem`
- 確認安全組允許你的 IP
- 確認實例正在運行

### 問題 2: Cron 任務未執行

**檢查**:
```bash
# 查看 cron 日誌
sudo tail -f /var/log/cron

# 確認 cron 服務運行
sudo systemctl status crond
```

**解決**:
```bash
# 啟動 cron 服務
sudo systemctl start crond
sudo systemctl enable crond

# 檢查腳本權限
ls -l /opt/globalping-checker/run_check.sh
chmod +x /opt/globalping-checker/run_check.sh
```

### 問題 3: S3 上傳失敗

**檢查**:
```bash
# 測試 S3 訪問
aws s3 ls s3://your-bucket/

# 檢查 IAM Role
aws sts get-caller-identity
```

**解決**:
- 確認 IAM Role 有 S3 權限
- 確認 Bucket 名稱正確
- 確認 Bucket 在同一區域

### 問題 4: 記憶體不足

**檢查**:
```bash
free -h
```

**解決**:
```bash
# 創建 swap 文件
sudo dd if=/dev/zero of=/swapfile bs=1M count=1024
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久啟用
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 🗑️ 刪除部署

### 刪除 CloudFormation Stack

```bash
aws cloudformation delete-stack \
  --stack-name GlobalpingCheckerEC2 \
  --region ap-northeast-1

# 等待刪除完成
aws cloudformation wait stack-delete-complete \
  --stack-name GlobalpingCheckerEC2 \
  --region ap-northeast-1
```

### 手動清理

```bash
# 終止 EC2 實例
aws ec2 terminate-instances --instance-ids i-xxxxx

# 刪除 Elastic IP
aws ec2 release-address --allocation-id eipalloc-xxxxx

# 刪除安全組
aws ec2 delete-security-group --group-id sg-xxxxx

# 刪除 Key Pair
aws ec2 delete-key-pair --key-name globalping-checker
```

## 📚 進階配置

### 使用 CloudWatch Agent

```bash
# 安裝 CloudWatch Agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
sudo rpm -U ./amazon-cloudwatch-agent.rpm

# 配置並啟動
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

### 設置告警

```bash
# CPU 使用率告警
aws cloudwatch put-metric-alarm \
  --alarm-name ec2-high-cpu \
  --alarm-description "EC2 CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=InstanceId,Value=i-xxxxx \
  --evaluation-periods 2
```

### 自動擴展 (可選)

如果需要處理大量域名，可以考慮使用 Auto Scaling Group。

## 📖 相關文檔

- [EC2 用戶指南](https://docs.aws.amazon.com/ec2/)
- [CloudFormation 文檔](https://docs.aws.amazon.com/cloudformation/)
- [Cron 表達式](https://crontab.guru/)
- [AWS 免費方案](https://aws.amazon.com/free/)

---

**創建時間**: 2026-03-06  
**維護者**: Globalping Checker Project
