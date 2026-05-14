# AWS EC2 連線指南

## 方法 1：SSH 連線（傳統方式）⭐

### 前置需求

1. **建立 Key Pair（如果還沒有）**

#### 在 AWS Console：
```
EC2 → Key Pairs → Create key pair
- Name: my-key-pair
- Key pair type: RSA
- Private key file format: .pem (Linux/Mac) 或 .ppk (Windows)
- 下載並妥善保管 .pem 檔案
```

#### 使用 AWS CLI：
```bash
# 建立 Key Pair
aws ec2 create-key-pair \
  --key-name my-key-pair \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/my-key-pair.pem

# 設定權限（重要！）
chmod 400 ~/.ssh/my-key-pair.pem
```

2. **啟動 EC2 實例時選擇 Key Pair**

在 Launch Instance 時，選擇你建立的 Key Pair。

3. **設定 Security Group（安全組）**

允許 SSH 連線：
- Type: SSH
- Protocol: TCP
- Port: 22
- Source: 
  - `0.0.0.0/0`（任何 IP，不建議生產環境）
  - 或你的 IP：`你的IP/32`（更安全）

### 連線步驟

#### macOS / Linux：

```bash
# 基本連線
ssh -i ~/.ssh/my-key-pair.pem ec2-user@<EC2-IP或Public-DNS>

# 範例
ssh -i ~/.ssh/my-key-pair.pem ec2-user@ec2-54-123-45-67.ap-northeast-1.compute.amazonaws.com

# 或使用 IP
ssh -i ~/.ssh/my-key-pair.pem ec2-user@54.123.45.67
```

**不同 AMI 的預設用戶名：**
- Amazon Linux / Amazon Linux 2: `ec2-user`
- Ubuntu: `ubuntu`
- Debian: `admin`
- RHEL / CentOS: `ec2-user`
- SUSE: `ec2-user`
- Fedora: `ec2-user`

#### Windows：

**使用 PowerShell 或 CMD：**
```powershell
# 使用 OpenSSH（Windows 10+）
ssh -i C:\path\to\my-key-pair.pem ec2-user@<EC2-IP>
```

**使用 PuTTY：**
1. 下載並安裝 [PuTTY](https://www.putty.org/)
2. 使用 PuTTYgen 將 .pem 轉換為 .ppk：
   - PuTTYgen → Load → 選擇 .pem 檔案
   - Save private key → 儲存為 .ppk
3. 在 PuTTY 中：
   - Host Name: `ec2-user@<EC2-IP>`
   - Connection → SSH → Auth → Credentials
   - Private key file: 選擇 .ppk 檔案
   - Open

### 簡化連線（設定 SSH Config）

建立或編輯 `~/.ssh/config`：

```bash
Host ec2-web
    HostName <EC2-Public-IP或DNS>
    User ec2-user
    IdentityFile ~/.ssh/my-key-pair.pem
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

然後直接使用：
```bash
ssh ec2-web
```

---

## 方法 2：AWS Systems Manager Session Manager（推薦，更安全）⭐

**優點：**
- ✅ 不需要開放 SSH port（22）
- ✅ 不需要管理 SSH keys
- ✅ 所有連線都有日誌記錄
- ✅ 支援 IAM 權限控制
- ✅ 可以連線到私有子網的實例

### 前置需求

1. **在 EC2 實例安裝 SSM Agent**

**Amazon Linux 2 / Amazon Linux：**
```bash
# SSM Agent 通常已預裝，確認狀態
sudo systemctl status amazon-ssm-agent

# 如果未安裝
sudo yum install -y amazon-ssm-agent
sudo systemctl enable amazon-ssm-agent
sudo systemctl start amazon-ssm-agent
```

**Ubuntu：**
```bash
sudo snap install amazon-ssm-agent --classic
sudo systemctl enable snap.amazon-ssm-agent.amazon-ssm-agent.service
sudo systemctl start snap.amazon-ssm-agent.amazon-ssm-agent.service
```

2. **EC2 實例需要 IAM Role 權限**

建立 IAM Role 並附加到 EC2 實例：

**IAM Policy：**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:UpdateInstanceInformation",
        "ssmmessages:CreateControlChannel",
        "ssmmessages:CreateDataChannel",
        "ssmmessages:OpenControlChannel",
        "ssmmessages:OpenDataChannel"
      ],
      "Resource": "*"
    }
  ]
}
```

**或使用 AWS 管理的 Policy：**
- `AmazonSSMManagedInstanceCore`

3. **安裝 AWS CLI 和 Session Manager Plugin**

```bash
# macOS
brew install awscli
brew install --cask session-manager-plugin

# 或下載安裝
# https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html
```

### 連線步驟

```bash
# 基本連線
aws ssm start-session --target <instance-id>

# 範例
aws ssm start-session --target i-0123456789abcdef0

# 使用 profile
aws ssm start-session --target <instance-id> --profile <profile-name>
```

**取得 Instance ID：**
```bash
# 列出所有實例
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,PublicIpAddress,State.Name]' --output table

# 或使用標籤過濾
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=my-server" \
  --query 'Reservations[*].Instances[*].[InstanceId,PublicIpAddress]' \
  --output table
```

### 使用 SSH 連線到 Session Manager（進階）

編輯 `~/.ssh/config`：

```
Host i-*
    ProxyCommand sh -c "aws ssm start-session --target %h --document-name AWS-StartSSHSession --parameters 'portNumber=%p'"
```

然後可以像一般 SSH 使用：
```bash
ssh ec2-user@i-0123456789abcdef0
```

---

## 方法 3：EC2 Instance Connect（瀏覽器內連線）

**優點：**
- ✅ 不需要 SSH key
- ✅ 直接在瀏覽器連線
- ✅ 自動管理臨時 SSH key

### 步驟：

1. 在 EC2 Console 選擇實例
2. 點擊 "Connect"
3. 選擇 "EC2 Instance Connect"
4. 點擊 "Connect"

**注意：** 需要實例支援 EC2 Instance Connect（較新的 AMI）

---

## 常見問題排除

### 問題 1：Permission denied (publickey)

**原因：** SSH key 權限或路徑錯誤

**解決：**
```bash
# 確認 key 檔案權限
chmod 400 ~/.ssh/my-key-pair.pem

# 確認 key 檔案路徑正確
ls -la ~/.ssh/my-key-pair.pem

# 使用完整路徑
ssh -i /完整/路徑/to/my-key-pair.pem ec2-user@<IP>
```

### 問題 2：Connection timed out

**原因：** Security Group 未開放 SSH 或 IP 被封鎖

**解決：**
1. 檢查 Security Group：
   ```bash
   aws ec2 describe-instances \
     --instance-ids i-0123456789abcdef0 \
     --query 'Reservations[0].Instances[0].SecurityGroups'
   ```

2. 檢查 Security Group 規則：
   ```bash
   aws ec2 describe-security-groups \
     --group-ids sg-0123456789abcdef0
   ```

3. 新增 SSH 規則：
   ```bash
   aws ec2 authorize-security-group-ingress \
     --group-id sg-0123456789abcdef0 \
     --protocol tcp \
     --port 22 \
     --cidr 0.0.0.0/0  # 或你的 IP/32
   ```

### 問題 3：Host key verification failed

**原因：** 實例 IP 改變，SSH 警告

**解決：**
```bash
# 從 known_hosts 移除舊的 key
ssh-keygen -R <EC2-IP>

# 或編輯 ~/.ssh/known_hosts 手動移除
```

### 問題 4：SSM Agent 未運行

**檢查狀態：**
```bash
# 在 EC2 實例上（需要先透過其他方式連線）
sudo systemctl status amazon-ssm-agent
```

**啟動服務：**
```bash
sudo systemctl start amazon-ssm-agent
sudo systemctl enable amazon-ssm-agent
```

### 問題 5：找不到實例 ID

**列出所有實例：**
```bash
aws ec2 describe-instances \
  --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],PublicIpAddress,State.Name]' \
  --output table
```

---

## 實用技巧

### 1. 使用 SSH Config 簡化連線

`~/.ssh/config`：
```
Host ec2-prod
    HostName 54.123.45.67
    User ec2-user
    IdentityFile ~/.ssh/my-key-pair.pem
    ServerAliveInterval 60
    ServerAliveCountMax 3
    LocalForward 8080 localhost:8080  # 端口轉發

Host ec2-dev
    HostName ec2-98-76-54-32.ap-northeast-1.compute.amazonaws.com
    User ubuntu
    IdentityFile ~/.ssh/dev-key.pem
```

使用：
```bash
ssh ec2-prod
```

### 2. SCP 傳輸檔案

```bash
# 上傳檔案到 EC2
scp -i ~/.ssh/my-key-pair.pem file.txt ec2-user@<IP>:/home/ec2-user/

# 下載檔案
scp -i ~/.ssh/my-key-pair.pem ec2-user@<IP>:/path/to/file.txt ./

# 上傳整個目錄
scp -i ~/.ssh/my-key-pair.pem -r ./local-folder ec2-user@<IP>:/home/ec2-user/
```

### 3. 端口轉發（Tunnel）

```bash
# 轉發本地 8080 到 EC2 的 80
ssh -i ~/.ssh/my-key-pair.pem -L 8080:localhost:80 ec2-user@<IP>

# 轉發 EC2 的 3306 到本地 3306（MySQL）
ssh -i ~/.ssh/my-key-pair.pem -L 3306:localhost:3306 ec2-user@<IP>
```

### 4. 使用 AWS CLI 快速連線腳本

建立 `connect-ec2.sh`：
```bash
#!/bin/bash

INSTANCE_ID=$1
if [ -z "$INSTANCE_ID" ]; then
    echo "用法: ./connect-ec2.sh <instance-id>"
    echo ""
    echo "可用的實例："
    aws ec2 describe-instances \
      --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],PublicIpAddress,State.Name]' \
      --output table
    exit 1
fi

# 嘗試使用 SSM Session Manager
if aws ssm start-session --target $INSTANCE_ID 2>/dev/null; then
    echo "使用 SSM Session Manager 連線"
else
    # 回退到 SSH
    IP=$(aws ec2 describe-instances \
      --instance-ids $INSTANCE_ID \
      --query 'Reservations[0].Instances[0].PublicIpAddress' \
      --output text)
    
    KEY_NAME=$(aws ec2 describe-instances \
      --instance-ids $INSTANCE_ID \
      --query 'Reservations[0].Instances[0].KeyName' \
      --output text)
    
    echo "使用 SSH 連線到 $IP"
    ssh -i ~/.ssh/${KEY_NAME}.pem ec2-user@$IP
fi
```

使用：
```bash
chmod +x connect-ec2.sh
./connect-ec2.sh i-0123456789abcdef0
```

---

## 安全建議

1. ✅ **使用 Session Manager**（不需要開放 SSH port）
2. ✅ **限制 Security Group**（只允許特定 IP）
3. ✅ **使用 IAM 角色**（不要使用 Access Key）
4. ✅ **定期更新系統**：
   ```bash
   # Amazon Linux
   sudo yum update -y
   
   # Ubuntu
   sudo apt update && sudo apt upgrade -y
   ```
5. ✅ **使用 SSH key 而非密碼**
6. ✅ **定期輪換 SSH keys**
7. ✅ **啟用 CloudTrail 記錄所有連線**

---

## 快速參考

### 取得實例資訊

```bash
# 列出所有實例
aws ec2 describe-instances \
  --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],PublicIpAddress,State.Name]' \
  --output table

# 取得特定實例的 IP
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text
```

### 常用 SSH 命令

```bash
# 基本連線
ssh -i ~/.ssh/key.pem ec2-user@<IP>

# 執行遠端命令
ssh -i ~/.ssh/key.pem ec2-user@<IP> "ls -la"

# 端口轉發
ssh -i ~/.ssh/key.pem -L 8080:localhost:80 ec2-user@<IP>

# 保持連線
ssh -i ~/.ssh/key.pem -o ServerAliveInterval=60 ec2-user@<IP>
```

---

## 下一步

- 📚 [AWS EC2 文件](https://docs.aws.amazon.com/ec2/)
- 📚 [AWS Systems Manager Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)
- 📚 [SSH 文件](https://www.ssh.com/academy/ssh)
