# AWS 部署故障排除指南

## 🔴 當前問題：代理連線失敗

### 問題描述
```
Failed to connect to proxy URL: "http://127.0.0.1:64634"
Could not connect to the endpoint URL
```

### 原因
你的系統設置了代理，但代理服務無法連線，導致 AWS CLI 無法訪問 AWS 服務。

## ✅ 解決方案

### 方法 1：使用環境檢查腳本（推薦）

```bash
cd ~/Desktop/Project/AWS-deploy
./check-environment.sh
```

這會檢查並修復所有環境問題。

### 方法 2：手動禁用代理

在**新的終端視窗**執行：

```bash
# 禁用代理
export http_proxy=""
export https_proxy=""
export HTTP_PROXY=""
export HTTPS_PROXY=""
export all_proxy=""
export ALL_PROXY=""

# 測試 AWS CLI
aws sts get-caller-identity

# 如果成功，執行部署
cd ~/Desktop/Project/AWS-deploy
./aws-manager.sh
```

### 方法 3：使用快速部署腳本

```bash
cd ~/Desktop/Project/AWS-deploy
./quick-deploy-globalping.sh
```

這個腳本會自動處理代理問題。

## 🔍 診斷步驟

### 1. 檢查代理設置

```bash
env | grep -i proxy
```

如果看到輸出，說明代理仍然啟用。

### 2. 測試 AWS CLI

```bash
aws sts get-caller-identity
```

應該看到你的 AWS 帳號資訊。

### 3. 檢查網路連線

```bash
ping aws.amazon.com
curl https://aws.amazon.com
```

### 4. 檢查 EC2 實例

```bash
aws ec2 describe-instances --region ap-northeast-1
```

## 🎯 完整部署流程

### 步驟 1：清理環境

```bash
# 開啟新的終端視窗
# 禁用代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
```

### 步驟 2：檢查環境

```bash
cd ~/Desktop/Project/AWS-deploy
./check-environment.sh
```

### 步驟 3：執行部署

```bash
./aws-manager.sh
# 選擇選項 2（部署 Globalping Checker）
```

## 🔧 常見問題

### Q1: 為什麼會有代理設置？

A: 可能是：
- 公司網路要求使用代理
- 之前安裝的軟體設置了代理
- VPN 或其他網路工具

### Q2: 如何永久禁用代理？

A: 編輯 shell 配置文件：

```bash
# 對於 zsh
nano ~/.zshrc

# 對於 bash
nano ~/.bashrc

# 添加以下內容
unset http_proxy
unset https_proxy
unset HTTP_PROXY
unset HTTPS_PROXY
unset all_proxy
unset ALL_PROXY
```

### Q3: 之前創建的實例怎麼辦？

A: 檢查實例狀態：

```bash
# 在禁用代理後執行
aws ec2 describe-instances \
  --region ap-northeast-1 \
  --filters "Name=tag:Name,Values=Globalping-Checker-Server"
```

如果實例存在但停止了：

```bash
# 啟動實例
aws ec2 start-instances --instance-ids i-xxxxx --region ap-northeast-1

# 或刪除並重新部署
aws ec2 terminate-instances --instance-ids i-xxxxx --region ap-northeast-1
```

### Q4: SSH 連線失敗怎麼辦？

A: 執行修復腳本：

```bash
./fix-ssh-connection.sh
```

## 📋 檢查清單

部署前確認：

- [ ] 代理已禁用（`env | grep -i proxy` 無輸出）
- [ ] AWS CLI 可以連線（`aws sts get-caller-identity` 成功）
- [ ] SSH 密鑰權限正確（`ls -la ~/.ssh/*.pem` 顯示 400）
- [ ] 在新的終端視窗執行

## 🚀 推薦部署流程

```bash
# 1. 開啟新終端視窗

# 2. 禁用代理
export http_proxy=""
export https_proxy=""
export all_proxy=""

# 3. 進入目錄
cd ~/Desktop/Project/AWS-deploy

# 4. 檢查環境
./check-environment.sh

# 5. 執行部署
./quick-deploy-globalping.sh
```

## 💡 提示

- 始終在**新的終端視窗**執行部署
- 確保代理完全禁用
- 如果問題持續，重啟終端或電腦
- 檢查 AWS 憑證是否正確配置

## 📞 獲取幫助

如果問題仍然存在：

1. 執行環境檢查：`./check-environment.sh`
2. 查看詳細錯誤訊息
3. 檢查 AWS Console 是否有實例創建

---

**更新時間**: 2026-03-06
