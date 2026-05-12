# Globalping Checker - AWS 部署總覽

本項目提供兩種 AWS 部署方案：**Lambda** 和 **EC2**

## 🎯 選擇部署方案

### Lambda 部署 (推薦新手)

**適合場景**:
- 定時檢測 (每天/每週)
- 域名數量 < 100
- 不需要持續運行
- 希望最小化成本

**優點**:
- ✅ 無需管理伺服器
- ✅ 自動擴展
- ✅ 按使用量付費
- ✅ 幾乎免費 (~$0.03/月)

**缺點**:
- ❌ 執行時間限制 (15 分鐘)
- ❌ 記憶體限制
- ❌ 較少控制權

**部署**:
```bash
cd aws/
./deploy.sh
```

📚 [Lambda 詳細文檔](aws/README.md)

---

### EC2 部署 (推薦進階用戶)

**適合場景**:
- 需要持續運行
- 域名數量 > 100
- 需要完整控制
- 複雜的自定義需求

**優點**:
- ✅ 完整控制權
- ✅ 無執行時間限制
- ✅ 可自定義環境
- ✅ 可安裝任何工具

**缺點**:
- ❌ 需要管理伺服器
- ❌ 固定成本 (~$9.59/月)
- ❌ 需要維護和更新

**部署**:
```bash
cd ec2/
./deploy-ec2.sh
```

📚 [EC2 詳細文檔](ec2/README.md)

---

## 📊 方案對比

| 特性 | Lambda | EC2 |
|------|--------|-----|
| **成本** | ~$0.03/月 | ~$9.59/月 |
| **免費額度** | 100 萬次請求/月 | 750 小時/月 (12 個月) |
| **執行時間** | 最多 15 分鐘 | 無限制 |
| **記憶體** | 最多 10 GB | 取決於實例類型 |
| **管理難度** | 簡單 | 中等 |
| **擴展性** | 自動 | 手動/Auto Scaling |
| **啟動時間** | 冷啟動 ~1 秒 | 立即 |
| **自定義** | 有限 | 完全 |

## 🚀 快速開始

### Lambda 部署 (3 步驟)

```bash
# 1. 配置 AWS CLI
aws configure

# 2. 部署
cd ~/Desktop/Project/GlobalpingChecker/aws
./deploy.sh

# 3. 上傳域名並測試
aws s3 cp ../test_2_domains.txt s3://globalping-checker-YOUR_ACCOUNT_ID/domains.txt
aws lambda invoke --function-name GlobalpingChecker output.json
```

### EC2 部署 (6 步驟)

```bash
# 1. 創建 SSH Key
aws ec2 create-key-pair --key-name globalping-checker \
  --query 'KeyMaterial' --output text > globalping-checker.pem
chmod 400 globalping-checker.pem

# 2. 部署 EC2
cd ~/Desktop/Project/GlobalpingChecker/ec2
./deploy-ec2.sh

# 3. 連線到 EC2
./connect.sh

# 4. 上傳項目 (在本地執行)
scp -i globalping-checker.pem -r ~/Desktop/Project/GlobalpingChecker ec2-user@YOUR_IP:~/

# 5. 安裝 (在 EC2 上執行)
cd ~/GlobalpingChecker/ec2
./setup.sh

# 6. 配置並測試
sudo nano /opt/globalping-checker/config.env
/opt/globalping-checker/run_check.sh
```

## 💡 建議

### 小規模使用 (< 50 域名)
→ 使用 **Lambda**，成本最低，管理最簡單

### 中規模使用 (50-200 域名)
→ 使用 **Lambda** 或 **EC2**，取決於檢測頻率

### 大規模使用 (> 200 域名)
→ 使用 **EC2**，更穩定可靠

### 測試階段
→ 使用 **Lambda**，快速部署和測試

### 生產環境
→ 根據需求選擇，建議 **EC2** 以獲得更好的控制

## 📁 目錄結構

```
GlobalpingChecker/
├── aws/                          # Lambda 部署
│   ├── cloudformation.yaml       # CloudFormation 模板
│   ├── lambda_function.py        # Lambda 函數
│   ├── deploy.sh                 # 部署腳本
│   ├── test_local.py            # 本地測試
│   ├── README.md                # 詳細文檔
│   └── QUICKSTART.md            # 快速開始
│
├── ec2/                          # EC2 部署
│   ├── cloudformation-ec2.yaml   # CloudFormation 模板
│   ├── setup.sh                  # 安裝腳本
│   ├── deploy-ec2.sh            # 部署腳本
│   ├── README.md                # 詳細文檔
│   └── QUICKSTART.md            # 快速開始
│
└── AWS_DEPLOYMENT.md            # 本文件
```

## 🔧 混合方案

你也可以同時使用兩種方案：

- **Lambda**: 定時檢測 (每天一次)
- **EC2**: 按需檢測 (手動觸發)

或者：

- **Lambda**: 輕量級檢測
- **EC2**: 深度分析和報告生成

## 💰 成本比較

### 每天檢測 100 個域名

| 方案 | 月成本 | 年成本 |
|------|--------|--------|
| Lambda | $0.03 | $0.36 |
| EC2 (t3.micro) | $9.59 | $115.08 |
| EC2 (免費方案) | $0.00 | $0.00 (前 12 個月) |

### 每小時檢測 100 個域名

| 方案 | 月成本 | 年成本 |
|------|--------|--------|
| Lambda | $0.72 | $8.64 |
| EC2 (t3.micro) | $9.59 | $115.08 |

## 📞 技術支援

### Lambda 相關問題
查看 [aws/README.md](aws/README.md)

### EC2 相關問題
查看 [ec2/README.md](ec2/README.md)

### 通用問題

**Q: 我應該選擇哪個方案？**
A: 如果不確定，先從 Lambda 開始。成本低，易於管理。

**Q: 可以遷移嗎？**
A: 可以。兩種方案使用相同的檢測腳本，可以輕鬆遷移。

**Q: 需要 Globalping API Token 嗎？**
A: 可選。免費配額通常足夠，但 Token 可以獲得更高配額。

**Q: 如何監控成本？**
A: 使用 AWS Cost Explorer 和設置預算告警。

**Q: 支援其他雲平台嗎？**
A: 目前只支援 AWS，但腳本可以在任何 Linux 環境運行。

## 🎓 學習資源

- [AWS Lambda 文檔](https://docs.aws.amazon.com/lambda/)
- [AWS EC2 文檔](https://docs.aws.amazon.com/ec2/)
- [Globalping API 文檔](https://www.jsdelivr.com/docs/api.globalping.io)
- [AWS 免費方案](https://aws.amazon.com/free/)

---

**創建時間**: 2026-03-06  
**維護者**: Globalping Checker Project

**開始部署**: 選擇 [Lambda](aws/QUICKSTART.md) 或 [EC2](ec2/QUICKSTART.md)
