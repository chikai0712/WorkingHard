# 快速開始 - 5 分鐘部署到 AWS

## 🎯 目標

將 Globalping 域名檢測系統部署到 AWS，實現自動化定時檢測。

## ⚡ 快速部署（3 步驟）

### 步驟 1: 配置 AWS CLI

```bash
# 如果還沒安裝 AWS CLI
brew install awscli  # macOS
# 或訪問: https://aws.amazon.com/cli/

# 配置憑證
aws configure
```

輸入你的 AWS 憑證：
- Access Key ID
- Secret Access Key  
- 預設區域: `ap-northeast-1` (東京) 或 `us-west-2` (俄勒岡)

### 步驟 2: 執行部署

```bash
cd ~/Desktop/Project/GlobalpingChecker/aws
./deploy.sh
```

部署腳本會詢問：
1. **Globalping API Token** (可選，直接按 Enter 跳過使用免費配額)
2. **通知 Email** (可選，接收檢測報告)
3. **執行排程** (預設每天凌晨 2 點)

### 步驟 3: 上傳域名並測試

```bash
# 上傳測試域名
aws s3 cp ../test_2_domains.txt s3://globalping-checker-YOUR_ACCOUNT_ID/domains.txt

# 手動觸發一次測試
aws lambda invoke --function-name GlobalpingChecker output.json

# 查看結果
cat output.json
```

## 🎉 完成！

系統已部署完成，會按照設定的排程自動執行檢測。

## 📊 查看結果

### 方法 1: 查看日誌

```bash
aws logs tail /aws/lambda/GlobalpingChecker --follow
```

### 方法 2: 下載結果文件

```bash
# 列出所有結果
aws s3 ls s3://globalping-checker-YOUR_ACCOUNT_ID/results/

# 下載最新結果
aws s3 cp s3://globalping-checker-YOUR_ACCOUNT_ID/results/ ./results/ --recursive
```

### 方法 3: Email 通知

如果配置了 Email，會自動收到檢測報告。

## 🔧 常用操作

### 更新域名列表

```bash
aws s3 cp your_domains.txt s3://globalping-checker-YOUR_ACCOUNT_ID/domains.txt
```

### 手動執行檢測

```bash
aws lambda invoke --function-name GlobalpingChecker output.json
```

### 暫停定時任務

```bash
aws events disable-rule --name GlobalpingCheckerSchedule
```

### 恢復定時任務

```bash
aws events enable-rule --name GlobalpingCheckerSchedule
```

### 刪除整個部署

```bash
aws cloudformation delete-stack --stack-name GlobalpingChecker
```

## 💰 成本

使用 AWS 免費方案，每天檢測 100 個域名：
- **月成本**: ~$0.03 USD (幾乎免費)

## 📚 詳細文檔

查看 [README.md](README.md) 了解更多配置選項和進階功能。

## ❓ 常見問題

### Q: 需要信用卡嗎？
A: 是的，AWS 需要信用卡註冊，但使用免費方案幾乎不會產生費用。

### Q: 可以在本地測試嗎？
A: 可以，執行 `./test_local.py` 進行本地測試。

### Q: 如何獲得 Globalping API Token？
A: 訪問 https://dash.globalping.io 註冊免費帳號。

### Q: 支援哪些 AWS 區域？
A: 所有 AWS 區域都支援，推薦使用 `ap-northeast-1` (東京)。

### Q: 可以檢測多少個域名？
A: Lambda 單次執行最多 15 分鐘，建議每次檢測不超過 100 個域名。

---

**需要幫助？** 查看 [README.md](README.md) 或檢查 CloudWatch Logs。
