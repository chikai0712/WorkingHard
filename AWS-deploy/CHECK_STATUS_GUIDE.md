# 🔍 檢查 AWS 運行狀況

## ⚠️ 重要：必須在系統終端執行

由於 Cursor IDE 會自動設置代理，導致 AWS CLI 無法連線。
請在**系統終端**（Terminal.app）執行檢查。

## 🚀 快速檢查（3 步驟）

### 步驟 1：開啟系統終端

```bash
# 方法 1：使用 Spotlight
按 Cmd + Space，輸入 "Terminal"，按 Enter

# 方法 2：使用 Finder
應用程式 > 工具程式 > 終端機
```

### 步驟 2：執行檢查腳本

```bash
cd ~/Desktop/Project/AWS-deploy
./check-status.sh
```

### 步驟 3：查看結果

腳本會顯示：
- ✅ AWS 連線狀態
- 📦 所有 EC2 實例
- 🟢 運行中的服務
- 💰 成本估算

## 📊 預期輸出

```
🔍 AWS 運行狀況檢查
========================================

1️⃣  檢查 AWS 連線...
   ✅ AWS CLI 連線正常
   帳號: 232313329609

2️⃣  檢查 EC2 實例...

   名稱                      狀態         IP 地址          類型         實例 ID
   ---------------------------------------------------------------------------------
   Globalping-Checker-Server 🟢 running   18.182.6.127    t3.micro     i-xxxxx

3️⃣  運行中實例詳情...

   📦 Globalping-Checker-Server
      實例 ID: i-xxxxx
      公網 IP: 18.182.6.127
      SSH Key: globalping-checker-key
      🔍 SSH 連線: ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@18.182.6.127
      📝 執行檢測: ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@18.182.6.127 '/opt/globalping-checker/run_check.sh'

4️⃣  檢查安全組...

   🔒 globalping-checker-sg (sg-xxxxx)

5️⃣  成本估算...

   運行中實例: 1
   停止的實例: 0
   預估月成本: ~$7.5 USD
   （假設 t3.micro 24/7 運行）

========================================
✅ 檢查完成
========================================
```

## 🔧 其他檢查命令

### 檢查特定服務

```bash
# Pokemon 遊戲
./check-game-status.sh

# Globalping Checker
./check-globalping-status.sh

# DNS 監控系統
./check-dns-monitoring-status.sh
```

### 使用統一管理界面

```bash
./aws-manager.sh
# 選擇選項 7（檢查所有服務狀態）
```

## 🐛 如果仍然失敗

### 檢查 1：AWS 憑證

```bash
aws configure list
```

應該顯示你的 Access Key 和 Region。

### 檢查 2：網路連線

```bash
ping aws.amazon.com
```

### 檢查 3：代理設置

```bash
env | grep -i proxy
```

應該沒有輸出或只有 `NO_PROXY`。

### 檢查 4：手動測試

```bash
# 完全禁用代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY

# 測試 AWS
aws sts get-caller-identity

# 查看實例
aws ec2 describe-instances --region ap-northeast-1
```

## 💡 快速操作

### 如果有運行中的實例

```bash
# 連線到 Globalping Checker
ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@YOUR_IP

# 執行檢測
/opt/globalping-checker/run_check.sh

# 查看日誌
tail -f /var/log/globalping-checker/check_*.log
```

### 如果實例已停止

```bash
# 啟動實例
aws ec2 start-instances --instance-ids i-xxxxx --region ap-northeast-1

# 或使用管理界面
./aws-manager.sh
# 選擇選項 12（啟動所有服務）
```

## 📞 需要幫助？

1. 執行 `./check-status.sh` 並截圖輸出
2. 執行 `aws configure list` 確認配置
3. 檢查是否在系統終端（非 Cursor）執行

---

**重要提醒**：所有 AWS 操作都必須在系統終端執行，不要在 Cursor 內建終端執行！
