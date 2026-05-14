# Globalping Checker - AWS 部署指南

## 📋 架構說明

此 AWS 部署方案包含以下組件：

- **Lambda Function**: 執行域名檢測邏輯
- **S3 Bucket**: 存儲域名列表和檢測結果
- **EventBridge**: 定時觸發檢測任務
- **SNS**: 發送檢測完成通知
- **CloudWatch Logs**: 記錄執行日誌

## 🚀 快速部署

### 前置需求

1. 安裝 AWS CLI
```bash
# macOS
brew install awscli

# 或下載安裝
# https://aws.amazon.com/cli/
```

2. 配置 AWS 憑證
```bash
aws configure
# 輸入 Access Key ID
# 輸入 Secret Access Key
# 輸入預設區域 (例如: ap-northeast-1)
```

### 一鍵部署

```bash
cd ~/Desktop/Project/GlobalpingChecker/aws
chmod +x deploy.sh
./deploy.sh
```

部署腳本會詢問：
- Globalping API Token (可選)
- 通知 Email 地址 (可選)
- 執行排程 (預設每天凌晨 2 點 UTC)

## 📝 使用步驟

### 1. 上傳域名列表

```bash
# 上傳測試域名
aws s3 cp ../test_2_domains.txt s3://globalping-checker-YOUR_ACCOUNT_ID/domains.txt

# 或上傳自己的域名列表
aws s3 cp your_domains.txt s3://globalping-checker-YOUR_ACCOUNT_ID/domains.txt
```

### 2. 手動觸發測試

```bash
# 手動執行一次
aws lambda invoke \
  --function-name GlobalpingChecker \
  --region ap-northeast-1 \
  output.json

# 查看輸出
cat output.json
```

### 3. 查看執行日誌

```bash
# 實時查看日誌
aws logs tail /aws/lambda/GlobalpingChecker --follow --region ap-northeast-1

# 查看最近 1 小時的日誌
aws logs tail /aws/lambda/GlobalpingChecker --since 1h --region ap-northeast-1
```

### 4. 查看檢測結果

```bash
# 列出所有結果
aws s3 ls s3://globalping-checker-YOUR_ACCOUNT_ID/results/ --recursive

# 下載最新結果
aws s3 cp s3://globalping-checker-YOUR_ACCOUNT_ID/results/ ./results/ --recursive

# 查看摘要報告
aws s3 cp s3://globalping-checker-YOUR_ACCOUNT_ID/results/summary_latest.txt - | cat
```

## ⚙️ 配置說明

### 修改執行排程

編輯 CloudFormation 參數：

```bash
aws cloudformation update-stack \
  --stack-name GlobalpingChecker \
  --use-previous-template \
  --parameters \
    ParameterKey=ScheduleExpression,ParameterValue="cron(0 */6 * * ? *)" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-northeast-1
```

常用排程表達式：
- `cron(0 2 * * ? *)` - 每天凌晨 2 點 (UTC)
- `cron(0 */6 * * ? *)` - 每 6 小時一次
- `cron(0 0 * * MON *)` - 每週一午夜
- `rate(1 day)` - 每天一次
- `rate(12 hours)` - 每 12 小時一次

### 更新 API Token

```bash
aws lambda update-function-configuration \
  --function-name GlobalpingChecker \
  --environment "Variables={S3_BUCKET_NAME=globalping-checker-YOUR_ACCOUNT_ID,DOMAINS_S3_KEY=domains.txt,SNS_TOPIC_ARN=YOUR_SNS_ARN,GLOBALPING_TOKEN=YOUR_NEW_TOKEN}" \
  --region ap-northeast-1
```

### 暫停/啟用定時任務

```bash
# 暫停
aws events disable-rule --name GlobalpingCheckerSchedule --region ap-northeast-1

# 啟用
aws events enable-rule --name GlobalpingCheckerSchedule --region ap-northeast-1
```

## 📊 監控與告警

### CloudWatch 指標

在 AWS Console 查看：
1. 進入 CloudWatch > Metrics
2. 選擇 Lambda > By Function Name
3. 查看 `GlobalpingChecker` 的指標

關鍵指標：
- **Invocations**: 執行次數
- **Duration**: 執行時間
- **Errors**: 錯誤次數
- **Throttles**: 限流次數

### 設置告警

```bash
# 創建錯誤告警
aws cloudwatch put-metric-alarm \
  --alarm-name GlobalpingChecker-Errors \
  --alarm-description "Lambda 執行錯誤" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=GlobalpingChecker \
  --region ap-northeast-1
```

## 💰 成本估算

基於每天執行一次，檢測 100 個域名：

| 服務 | 用量 | 月成本 (USD) |
|------|------|-------------|
| Lambda | ~5 分鐘/天 × 30 天 = 150 分鐘 | $0.00 (免費額度) |
| S3 | ~10 MB 存儲 + 少量請求 | $0.00 (免費額度) |
| CloudWatch Logs | ~50 MB/月 | $0.03 |
| SNS | 30 封 Email | $0.00 (免費額度) |
| **總計** | | **~$0.03/月** |

> 註：AWS 免費方案包含：
> - Lambda: 每月 100 萬次請求 + 40 萬 GB-秒
> - S3: 5 GB 存儲 + 20,000 GET 請求
> - SNS: 1,000 封 Email

## 🔧 故障排除

### 問題 1: Lambda 超時

**錯誤**: Task timed out after 900.00 seconds

**解決方案**:
```bash
# 增加超時時間到 15 分鐘
aws lambda update-function-configuration \
  --function-name GlobalpingChecker \
  --timeout 900 \
  --region ap-northeast-1
```

### 問題 2: 記憶體不足

**錯誤**: Process exited before completing request

**解決方案**:
```bash
# 增加記憶體到 1024 MB
aws lambda update-function-configuration \
  --function-name GlobalpingChecker \
  --memory-size 1024 \
  --region ap-northeast-1
```

### 問題 3: S3 權限錯誤

**錯誤**: Access Denied

**解決方案**:
檢查 Lambda 執行角色是否有 S3 權限：
```bash
aws iam get-role-policy \
  --role-name GlobalpingCheckerLambdaRole \
  --policy-name S3Access \
  --region ap-northeast-1
```

### 問題 4: API 配額用完

**錯誤**: You only have X credits remaining

**解決方案**:
1. 使用 API Token (更高配額)
2. 減少檢測頻率
3. 減少每次檢測的域名數量

## 🔄 更新部署

### 更新 Lambda 代碼

```bash
cd ~/Desktop/Project/GlobalpingChecker/aws

# 修改 lambda_function.py 後重新部署
./deploy.sh
```

### 更新 CloudFormation 模板

```bash
aws cloudformation update-stack \
  --stack-name GlobalpingChecker \
  --template-body file://cloudformation.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-northeast-1
```

## 🗑️ 刪除部署

```bash
# 刪除 CloudFormation Stack
aws cloudformation delete-stack \
  --stack-name GlobalpingChecker \
  --region ap-northeast-1

# 等待刪除完成
aws cloudformation wait stack-delete-complete \
  --stack-name GlobalpingChecker \
  --region ap-northeast-1

# 手動刪除 S3 Bucket (如果需要)
aws s3 rb s3://globalping-checker-YOUR_ACCOUNT_ID --force
aws s3 rb s3://globalping-deploy-YOUR_ACCOUNT_ID --force
```

## 📚 進階配置

### 多區域部署

```bash
# 部署到多個區域
for region in ap-northeast-1 us-west-2 eu-west-1; do
  aws cloudformation deploy \
    --template-file cloudformation.yaml \
    --stack-name GlobalpingChecker \
    --region $region \
    --capabilities CAPABILITY_NAMED_IAM
done
```

### 自定義檢測邏輯

編輯 `lambda_function.py` 中的 `check_domains()` 函數：

```python
def check_domains(domains: List[str]) -> Dict[str, Any]:
    # 自定義檢測邏輯
    # 例如：增加重試次數、修改延遲時間等
    pass
```

### 整合其他服務

- **DynamoDB**: 存儲歷史檢測記錄
- **API Gateway**: 提供 REST API 接口
- **Step Functions**: 編排複雜的檢測流程
- **SQS**: 處理大量域名的異步檢測

## 📞 技術支援

### 查看 CloudFormation 事件

```bash
aws cloudformation describe-stack-events \
  --stack-name GlobalpingChecker \
  --region ap-northeast-1 \
  --max-items 20
```

### 查看 Lambda 配置

```bash
aws lambda get-function-configuration \
  --function-name GlobalpingChecker \
  --region ap-northeast-1
```

### 測試 Lambda 函數

```bash
# 使用測試事件
aws lambda invoke \
  --function-name GlobalpingChecker \
  --payload '{"test": true}' \
  --region ap-northeast-1 \
  output.json
```

## 🎯 最佳實踐

1. **使用 API Token**: 獲得更高的 API 配額
2. **合理設置排程**: 避免過於頻繁的檢測
3. **監控成本**: 定期檢查 AWS Cost Explorer
4. **備份結果**: 定期下載 S3 中的檢測結果
5. **日誌保留**: 設置合理的 CloudWatch Logs 保留期限
6. **版本控制**: 使用 Lambda 版本和別名管理代碼

## 📖 相關文檔

- [AWS Lambda 文檔](https://docs.aws.amazon.com/lambda/)
- [AWS CloudFormation 文檔](https://docs.aws.amazon.com/cloudformation/)
- [Globalping API 文檔](https://www.jsdelivr.com/docs/api.globalping.io)
- [EventBridge Cron 表達式](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html)

---

**創建時間**: 2026-03-06  
**維護者**: Globalping Checker Project
