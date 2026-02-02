# AWS 憑證設定指南

## 什麼是 AWS Access Key ID？

**AWS Access Key ID** 和 **AWS Secret Access Key** 是一組憑證，用來讓 AWS CLI 或其他工具存取你的 AWS 帳號。

類似於：
- **Access Key ID** = 用戶名
- **Secret Access Key** = 密碼

---

## 如何取得 AWS Access Key？

### 方法 1：在 AWS Console 建立（推薦）

#### 步驟：

1. **登入 AWS Console**
   - 前往 [AWS Console](https://console.aws.amazon.com)
   - 使用你的 AWS 帳號登入

2. **進入 Security Credentials**
   - 點擊右上角你的用戶名
   - 選擇 "Security credentials"（安全憑證）

3. **建立 Access Key**
   - 向下滾動到 "Access keys" 區塊
   - 點擊 "Create access key"（建立存取金鑰）

4. **選擇使用案例**
   - 選擇 "Command Line Interface (CLI)"
   - 勾選確認框
   - 點擊 "Next"

5. **設定描述標籤（可選）**
   - 輸入描述，例如：`My MacBook CLI`
   - 點擊 "Create access key"

6. **下載或複製憑證**
   - ⚠️ **重要**：Secret Access Key 只會顯示一次！
   - 點擊 "Download .csv file" 下載
   - 或複製 Access Key ID 和 Secret Access Key
   - 妥善保存，不要分享給他人

### 方法 2：使用 IAM 用戶建立（更安全，推薦生產環境）

1. **建立 IAM 用戶**
   - IAM → Users → Create user
   - 用戶名：`cli-user`（自訂）
   - 選擇 "Provide user access to the AWS Management Console"（可選）
   - 或只選擇 "Access key - Programmatic access"

2. **設定權限**
   - 選擇 "Attach policies directly"
   - 選擇需要的權限（例如：`AdministratorAccess` 或自訂權限）

3. **建立 Access Key**
   - 完成後，在用戶頁面 → Security credentials
   - Create access key → CLI
   - 下載或複製憑證

---

## 設定 AWS CLI

### 執行 aws configure

```bash
aws configure
```

會詢問以下資訊：

1. **AWS Access Key ID**
   ```
   AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
   ```
   - 輸入你剛才複製的 Access Key ID
   - 格式類似：`AKIA...`（20 個字元）

2. **AWS Secret Access Key**
   ```
   AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
   ```
   - 輸入你剛才複製的 Secret Access Key
   - 格式類似：`wJalr...`（40 個字元）
   - ⚠️ 輸入時不會顯示（安全考量）

3. **Default region name**
   ```
   Default region name [None]: ap-northeast-1
   ```
   - 建議輸入：`ap-northeast-1`（東京，適合台灣）
   - 其他選項：
     - `us-east-1`（維吉尼亞）
     - `us-west-2`（奧勒岡）
     - `eu-west-1`（愛爾蘭）

4. **Default output format**
   ```
   Default output format [None]: json
   ```
   - 建議輸入：`json`
   - 其他選項：`text`、`table`、`yaml`

### 完整範例

```
$ aws configure
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name [None]: ap-northeast-1
Default output format [None]: json
```

---

## 驗證設定

```bash
# 測試連線
aws sts get-caller-identity

# 應該會顯示類似：
# {
#     "UserId": "AIDAIOSFODNN7EXAMPLE",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/your-username"
# }
```

如果成功，表示設定正確！

---

## 安全注意事項

### ⚠️ 重要安全建議

1. **不要分享 Access Key**
   - 不要上傳到 GitHub
   - 不要分享給他人
   - 不要放在公開的地方

2. **使用 IAM 用戶而非 Root 帳號**
   - Root 帳號的 Access Key 權限太大
   - 建議建立 IAM 用戶並給予最小必要權限

3. **定期輪換 Access Key**
   - 每 90 天更換一次
   - 如果懷疑洩露，立即刪除並建立新的

4. **使用環境變數（可選）**
   ```bash
   export AWS_ACCESS_KEY_ID="your-access-key"
   export AWS_SECRET_ACCESS_KEY="your-secret-key"
   export AWS_DEFAULT_REGION="ap-northeast-1"
   ```

5. **使用 AWS Profiles（多帳號管理）**
   ```bash
   aws configure --profile work
   aws configure --profile personal
   
   # 使用特定 profile
   aws s3 ls --profile work
   ```

---

## 常見問題

### Q: Access Key ID 格式是什麼？

**A:** 格式類似：
- 開頭：`AKIA`（IAM 用戶）或 `ASIA`（臨時憑證）
- 長度：20 個字元
- 範例：`AKIAIOSFODNN7EXAMPLE`

### Q: Secret Access Key 格式是什麼？

**A:** 格式類似：
- 長度：40 個字元
- 包含大小寫字母、數字、特殊字元
- 範例：`wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`

### Q: 輸入 Secret Access Key 時沒有顯示？

**A:** 這是正常的！為了安全，終端機不會顯示密碼輸入。

### Q: 忘記 Secret Access Key 怎麼辦？

**A:** Secret Access Key 只會顯示一次，如果忘記：
1. 刪除舊的 Access Key
2. 建立新的 Access Key
3. 重新執行 `aws configure`

### Q: 可以有多組 Access Key 嗎？

**A:** 可以！每個 IAM 用戶最多可以有 2 組 Access Key。這對輪換很有用。

---

## 設定多個 AWS 帳號（使用 Profiles）

```bash
# 設定工作帳號
aws configure --profile work
# 輸入 work 帳號的 Access Key

# 設定個人帳號
aws configure --profile personal
# 輸入 personal 帳號的 Access Key

# 使用特定 profile
aws s3 ls --profile work
aws ec2 describe-instances --profile personal

# 設定預設 profile
export AWS_PROFILE=work
```

---

## 檢查目前的設定

```bash
# 查看目前設定的 Access Key ID（部分顯示）
aws configure get aws_access_key_id

# 查看區域
aws configure get region

# 查看所有設定
cat ~/.aws/credentials
cat ~/.aws/config
```

---

## 更新或刪除憑證

```bash
# 更新憑證
aws configure

# 或手動編輯
nano ~/.aws/credentials

# 刪除憑證（刪除檔案）
rm ~/.aws/credentials
rm ~/.aws/config
```

---

## 下一步

設定完成後：

```bash
# 1. 驗證設定
aws sts get-caller-identity

# 2. 執行設定腳本
cd ~/Desktop/Project/Website
./setup-aws-key.sh
```

---

## 快速參考

| 項目 | 說明 | 範例 |
|------|------|------|
| **Access Key ID** | 類似用戶名 | `AKIAIOSFODNN7EXAMPLE` |
| **Secret Access Key** | 類似密碼 | `wJalrXUtnFEMI/K7MDENG/...` |
| **Region** | AWS 區域 | `ap-northeast-1`（東京） |
| **Output Format** | 輸出格式 | `json`（推薦） |

---

## 取得 Access Key 的完整步驟（圖文說明）

### 在 AWS Console：

1. **右上角** → 點擊你的用戶名
2. **Security credentials**
3. 向下滾動到 **"Access keys"**
4. **Create access key**
5. 選擇 **"Command Line Interface (CLI)"**
6. 勾選確認 → **Next**
7. 可選：輸入描述標籤 → **Create access key**
8. **下載 .csv** 或複製兩個值：
   - Access Key ID
   - Secret Access Key

---

## 安全檢查清單

- [ ] 使用 IAM 用戶而非 Root 帳號
- [ ] Access Key 權限最小化（只給必要權限）
- [ ] 不要上傳到 Git
- [ ] 定期輪換（每 90 天）
- [ ] 使用 MFA（多因素驗證）
- [ ] 監控 Access Key 使用情況

---

## 需要幫助？

如果遇到問題：
1. 確認 Access Key 格式正確（20 和 40 個字元）
2. 確認 Access Key 未過期或被刪除
3. 確認 IAM 用戶有正確權限
4. 檢查網路連線
