# AWS CLI 安裝指南

## macOS 安裝

### 方法 1：使用 Homebrew（推薦）

```bash
# 安裝 Homebrew（如果還沒有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安裝 AWS CLI
brew install awscli

# 驗證安裝
aws --version
```

### 方法 2：使用安裝程式

```bash
# 下載安裝程式
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"

# 安裝
sudo installer -pkg AWSCLIV2.pkg -target /

# 驗證
aws --version
```

### 方法 3：使用 pip

```bash
# 安裝 pip（如果還沒有）
python3 -m ensurepip --upgrade

# 安裝 AWS CLI
pip3 install awscli --upgrade

# 驗證
aws --version
```

---

## Linux 安裝

### 方法 1：使用安裝程式（推薦）

```bash
# 下載
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

# 解壓縮
unzip awscliv2.zip

# 安裝
sudo ./aws/install

# 驗證
aws --version
```

### 方法 2：使用套件管理器

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install awscli

# CentOS/RHEL
sudo yum install awscli

# Fedora
sudo dnf install awscli
```

---

## Windows 安裝

### 方法 1：使用 MSI 安裝程式

1. 下載：https://awscli.amazonaws.com/AWSCLIV2.msi
2. 執行安裝程式
3. 開啟 PowerShell 或 CMD
4. 驗證：`aws --version`

### 方法 2：使用 Chocolatey

```powershell
choco install awscli
```

---

## 配置 AWS CLI

安裝完成後，需要配置 AWS 憑證：

```bash
aws configure
```

會詢問以下資訊：

1. **AWS Access Key ID**: 你的 Access Key
2. **AWS Secret Access Key**: 你的 Secret Key
3. **Default region name**: 預設區域（例如：`ap-northeast-1`）
4. **Default output format**: 輸出格式（建議：`json`）

### 取得 AWS Access Key

1. 登入 AWS Console
2. 右上角點擊你的用戶名 → Security credentials
3. Access keys → Create access key
4. 下載或複製 Access Key ID 和 Secret Access Key

⚠️ **重要**：Secret Access Key 只會顯示一次，請妥善保存！

---

## 驗證安裝

```bash
# 檢查版本
aws --version

# 測試連線
aws sts get-caller-identity

# 應該會顯示你的 AWS 帳號資訊
```

---

## 故障排除

### 問題：command not found

**解決：**
```bash
# 檢查 PATH
echo $PATH

# 手動加入 PATH（macOS/Linux）
export PATH=$PATH:/usr/local/bin

# 或加入 ~/.zshrc 或 ~/.bashrc
echo 'export PATH=$PATH:/usr/local/bin' >> ~/.zshrc
source ~/.zshrc
```

### 問題：權限錯誤

**解決：**
```bash
# macOS/Linux
sudo chown -R $(whoami) /usr/local/aws-cli
```

---

## 下一步

安裝完成後，執行：

```bash
# 配置 AWS 憑證
aws configure

# 測試設定腳本
cd Website
./setup-aws-key.sh
```
