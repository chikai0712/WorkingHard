# AWS 金鑰連線設定完整指南

## 步驟 1：建立 AWS Key Pair

### 方法 A：在 AWS Console 建立（推薦新手）

1. **登入 AWS Console**
   - 前往 [AWS Console](https://console.aws.amazon.com)

2. **建立 Key Pair**
   ```
   EC2 → Key Pairs → Create key pair
   ```

3. **設定選項**
   - **Name**: `my-ec2-key`（自訂名稱）
   - **Key pair type**: `RSA`
   - **Private key file format**: 
     - `.pem`（macOS/Linux）
     - `.ppk`（Windows PuTTY）
   - **Key size**: `2048` 或 `4096`

4. **下載並保存**
   - 點擊 "Create key pair"
   - 檔案會自動下載（例如：`my-ec2-key.pem`）
   - ⚠️ **重要**：此檔案只能下載一次，請妥善保管！

### 方法 B：使用 AWS CLI 建立

```bash
# 建立 Key Pair
aws ec2 create-key-pair \
  --key-name my-ec2-key \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/my-ec2-key.pem

# 設定正確權限（必須！）
chmod 400 ~/.ssh/my-ec2-key.pem

# 確認檔案已建立
ls -la ~/.ssh/my-ec2-key.pem
```

---

## 步驟 2：設定 SSH Key 權限（macOS/Linux）

```bash
# 移動到 .ssh 目錄（如果不在）
mkdir -p ~/.ssh
mv ~/Downloads/my-ec2-key.pem ~/.ssh/

# 設定權限（非常重要！）
chmod 400 ~/.ssh/my-ec2-key.pem

# 確認權限
ls -la ~/.ssh/my-ec2-key.pem
# 應該顯示：-r--------
```

**為什麼需要 chmod 400？**
- SSH 會拒絕權限過於開放的 key 檔案
- 400 = 只有擁有者可讀取

---

## 步驟 3：啟動 EC2 實例時選擇 Key Pair

### 在 Launch Instance 時：

1. **選擇 Key Pair**
   - 在 "Key pair (login)" 下拉選單
   - 選擇你剛建立的 key pair（例如：`my-ec2-key`）

2. **設定 Security Group**
   - 確保允許 SSH（port 22）
   - Source: 
     - `My IP`（推薦，只允許你的 IP）
     - 或 `0.0.0.0/0`（任何 IP，不建議）

3. **啟動實例**

---

## 步驟 4：取得 EC2 實例資訊

### 方法 A：AWS Console

1. EC2 → Instances
2. 選擇你的實例
3. 查看：
   - **Public IPv4 address**（公網 IP）
   - **Instance ID**（例如：`i-0123456789abcdef0`）

### 方法 B：AWS CLI

```bash
# 列出所有實例
aws ec2 describe-instances \
  --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],PublicIpAddress,State.Name,KeyName]' \
  --output table

# 取得特定實例的 IP
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text
```

---

## 步驟 5：測試連線

### 基本 SSH 連線

```bash
# 格式
ssh -i ~/.ssh/<key-name>.pem <username>@<EC2-IP>

# 範例（Amazon Linux）
ssh -i ~/.ssh/my-ec2-key.pem ec2-user@54.123.45.67

# 範例（Ubuntu）
ssh -i ~/.ssh/my-ec2-key.pem ubuntu@54.123.45.67
```

**不同 AMI 的預設用戶名：**
- Amazon Linux / Amazon Linux 2: `ec2-user`
- Ubuntu: `ubuntu`
- Debian: `admin`
- RHEL / CentOS: `ec2-user`
- SUSE: `ec2-user`
- Fedora: `ec2-user`

### 如果連線成功

你會看到類似：
```
The authenticity of host '54.123.45.67' can't be established.
ECDSA key fingerprint is SHA256:...
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes

       __|  __|_  )
       _|  (     /   Amazon Linux 2 AMI
      ___|\___|___|

[ec2-user@ip-172-31-0-1 ~]$
```

---

## 步驟 6：簡化連線（設定 SSH Config）

建立或編輯 `~/.ssh/config`：

```bash
nano ~/.ssh/config
# 或
vim ~/.ssh/config
```

加入以下內容：

```
Host ec2-web
    HostName 54.123.45.67
    User ec2-user
    IdentityFile ~/.ssh/my-ec2-key.pem
    ServerAliveInterval 60
    ServerAliveCountMax 3

Host ec2-dev
    HostName ec2-98-76-54-32.ap-northeast-1.compute.amazonaws.com
    User ubuntu
    IdentityFile ~/.ssh/my-ec2-key.pem
```

**設定權限：**
```bash
chmod 600 ~/.ssh/config
```

**使用：**
```bash
# 直接使用簡短名稱
ssh ec2-web
```

---

## 常見問題排除

### ❌ 問題 1：Permission denied (publickey)

**錯誤訊息：**
```
Permission denied (publickey)
```

**原因：**
- Key 檔案權限錯誤
- Key 檔案路徑錯誤
- 使用了錯誤的用戶名

**解決：**
```bash
# 1. 確認 key 檔案權限
chmod 400 ~/.ssh/my-ec2-key.pem

# 2. 確認檔案存在
ls -la ~/.ssh/my-ec2-key.pem

# 3. 使用完整路徑
ssh -i /完整/路徑/to/my-ec2-key.pem ec2-user@<IP>

# 4. 使用 -v 查看詳細錯誤
ssh -v -i ~/.ssh/my-ec2-key.pem ec2-user@<IP>
```

### ❌ 問題 2：Connection timed out

**錯誤訊息：**
```
ssh: connect to host 54.123.45.67 port 22: Connection timed out
```

**原因：**
- Security Group 未開放 port 22
- 實例沒有 Public IP
- 實例未運行

**解決：**
```bash
# 1. 檢查實例狀態
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[0].Instances[0].State.Name'

# 2. 檢查 Security Group
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[0].Instances[0].SecurityGroups[*].GroupId'

# 3. 新增 SSH 規則（替換 sg-xxx 為實際的 Security Group ID）
aws ec2 authorize-security-group-ingress \
  --group-id sg-0123456789abcdef0 \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0  # 或你的 IP/32（更安全）
```

### ❌ 問題 3：WARNING: UNPROTECTED PRIVATE KEY FILE!

**錯誤訊息：**
```
WARNING: UNPROTECTED PRIVATE KEY FILE!
Permissions 0644 for 'my-ec2-key.pem' are too open.
```

**解決：**
```bash
chmod 400 ~/.ssh/my-ec2-key.pem
```

### ❌ 問題 4：找不到 key pair

**錯誤訊息：**
```
Could not resolve hostname
```

**解決：**
```bash
# 確認 key pair 名稱
aws ec2 describe-key-pairs

# 確認實例使用的 key pair
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[0].Instances[0].KeyName'
```

---

## 安全最佳實踐

### ✅ 1. 限制 Security Group

不要使用 `0.0.0.0/0`，改為你的 IP：

```bash
# 取得你的 IP
curl ifconfig.me

# 只允許你的 IP
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxx \
  --protocol tcp \
  --port 22 \
  --cidr $(curl -s ifconfig.me)/32
```

### ✅ 2. 使用多個 Key Pair

為不同環境使用不同的 key：
- `production-key.pem` - 生產環境
- `development-key.pem` - 開發環境
- `staging-key.pem` - 測試環境

### ✅ 3. 定期輪換 Key Pair

```bash
# 建立新 key
aws ec2 create-key-pair --key-name my-ec2-key-v2 > new-key.pem

# 在實例上更新 authorized_keys
# 然後刪除舊 key（在確認新 key 可用後）
```

### ✅ 4. 備份 Key Pair

```bash
# 備份到安全位置
cp ~/.ssh/my-ec2-key.pem ~/backups/
chmod 400 ~/backups/my-ec2-key.pem
```

### ✅ 5. 使用 AWS Systems Manager（更安全）

不需要開放 SSH port，使用 Session Manager：

```bash
aws ssm start-session --target i-0123456789abcdef0
```

---

## 快速檢查清單

- [ ] Key Pair 已建立並下載
- [ ] Key 檔案權限設為 400 (`chmod 400`)
- [ ] Key 檔案放在 `~/.ssh/` 目錄
- [ ] EC2 實例啟動時選擇了正確的 Key Pair
- [ ] Security Group 開放 port 22
- [ ] 實例有 Public IP（或使用 Session Manager）
- [ ] 使用正確的用戶名（ec2-user / ubuntu）
- [ ] 實例狀態為 "running"

---

## 下一步

連線成功後，你可以：

1. **更新系統**
   ```bash
   # Amazon Linux
   sudo yum update -y
   
   # Ubuntu
   sudo apt update && sudo apt upgrade -y
   ```

2. **安裝常用工具**
   ```bash
   # Amazon Linux
   sudo yum install -y git vim htop
   
   # Ubuntu
   sudo apt install -y git vim htop
   ```

3. **設定防火牆**
   ```bash
   # 查看狀態
   sudo systemctl status firewalld  # RHEL/CentOS
   sudo ufw status                   # Ubuntu
   ```

4. **部署你的應用**
   - 使用 SCP 上傳檔案
   - 使用 Git 拉取程式碼
   - 設定服務自動啟動

---

## 實用命令參考

```bash
# 列出所有 Key Pairs
aws ec2 describe-key-pairs

# 刪除 Key Pair（僅刪除 AWS 中的記錄，不刪除本地檔案）
aws ec2 delete-key-pair --key-name my-ec2-key

# 列出所有實例及其 Key Pair
aws ec2 describe-instances \
  --query 'Reservations[*].Instances[*].[InstanceId,KeyName,PublicIpAddress]' \
  --output table

# 測試連線（不實際登入）
ssh -i ~/.ssh/my-ec2-key.pem -o ConnectTimeout=5 ec2-user@<IP> echo "連線成功"
```
