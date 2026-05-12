# 🔧 SSH 連線問題解決方案

## 問題診斷

當前問題：SSH 連線被拒絕（Operation not permitted）

可能原因：
1. ✅ 密鑰權限正確（已確認）
2. ❌ 網路連線被阻擋（代理或防火牆）
3. ❓ AWS 實例狀態未知
4. ❓ AWS 安全組設置

## 🚀 解決方案

### 方案 1：在新終端視窗手動部署（推薦）

打開一個**新的終端視窗**（不是在 Cursor 內），然後執行：

```bash
# 1. 禁用代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY
unset socks_proxy SOCKS_PROXY socks5_proxy SOCKS5_PROXY

# 2. 測試 SSH 連線
ssh -i ~/.ssh/globalping-checker-key.pem ubuntu@54.238.247.106

# 如果連線成功，繼續以下步驟：

# 3. 在本地打包（在另一個終端視窗）
cd ~/Desktop/Project/GlobalpingChecker
tar -czf v4.1-update.tar.gz v4.1/

# 4. 上傳到 AWS
scp -i ~/.ssh/globalping-checker-key.pem v4.1-update.tar.gz ubuntu@54.238.247.106:~/

# 5. SSH 到 AWS 並部署
ssh -i ~/.ssh/globalping-checker-key.pem ubuntu@54.238.247.106

# 在 AWS 上執行：
cd ~/v4.1
docker-compose down

# 備份
cp .env /tmp/v4.1.env.backup
cp domains.txt /tmp/v4.1.domains.backup
cd ~
mv v4.1 v4.1-backup-$(date +%Y%m%d-%H%M%S)

# 解壓並配置
tar -xzf v4.1-update.tar.gz
cd v4.1
cp /tmp/v4.1.env.backup .env
cp /tmp/v4.1.domains.backup domains.txt

# 啟動服務
docker-compose up -d --build

# 查看日誌
docker-compose logs -f --tail=50
```

### 方案 2：檢查 AWS 實例狀態

```bash
# 在新終端視窗執行
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY

# 檢查實例狀態
aws ec2 describe-instances \
    --region ap-northeast-1 \
    --filters "Name=tag:Name,Values=Globalping-V4.1-Tokyo" \
    --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress]' \
    --output table

# 如果實例停止，啟動它
aws ec2 start-instances --region ap-northeast-1 --instance-ids <INSTANCE_ID>
```

### 方案 3：檢查安全組設置

```bash
# 獲取安全組 ID
aws ec2 describe-instances \
    --region ap-northeast-1 \
    --filters "Name=tag:Name,Values=Globalping-V4.1-Tokyo" \
    --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
    --output text

# 檢查安全組規則
aws ec2 describe-security-groups \
    --region ap-northeast-1 \
    --group-ids <SECURITY_GROUP_ID>

# 如果 SSH (port 22) 沒有開放，添加規則
aws ec2 authorize-security-group-ingress \
    --region ap-northeast-1 \
    --group-id <SECURITY_GROUP_ID> \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0
```

### 方案 4：使用 AWS Console

1. 登入 AWS Console
2. 前往 EC2 → Instances
3. 找到 "Globalping-V4.1-Tokyo" 實例
4. 檢查：
   - 實例狀態（應該是 Running）
   - 公網 IP（應該是 54.238.247.106）
   - 安全組（應該允許 SSH port 22）
5. 如果需要，修改安全組規則

## 📝 部署文件已準備

打包文件位置：
```
~/Desktop/Project/GlobalpingChecker/v4.1-update.tar.gz
```

部署腳本位置：
```
~/Desktop/Project/GlobalpingChecker/deploy-v4.1-no-proxy.sh
```

## 🎯 快速測試

在**新終端視窗**執行：

```bash
# 禁用代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY

# 測試連線
ssh -i ~/.ssh/globalping-checker-key.pem ubuntu@54.238.247.106 "echo 'SSH OK'"
```

如果顯示 "SSH OK"，說明連線成功，可以繼續部署。

## 💡 建議

1. **使用系統終端**（Terminal.app 或 iTerm），不要在 Cursor 內執行
2. **確保禁用代理**
3. **檢查 AWS 實例狀態**
4. **如果還是失敗，提供錯誤訊息**

## 📞 需要幫助？

如果以上方法都不行，請提供：
1. SSH 錯誤訊息的完整輸出
2. AWS 實例狀態截圖
3. 安全組設置截圖

我會根據具體情況提供進一步的解決方案。
