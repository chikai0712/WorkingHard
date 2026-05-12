# AWS 兩種金鑰說明

## 🔑 兩種不同的金鑰

AWS 有兩種不同的金鑰，用途完全不同：

---

## 1️⃣ AWS CLI Access Key（剛才設定的）

### 用途
- **用於 API 認證**：讓 AWS CLI 可以呼叫 AWS API
- **用於程式存取**：讓應用程式可以存取 AWS 服務

### 設定位置
- 剛才執行的 `aws configure` 就是設定這個
- 儲存在：`~/.aws/credentials`

### 包含什麼
- **Access Key ID**：例如 `AKIAIOSFODNN7EXAMPLE`
- **Secret Access Key**：例如 `wJalrXUtnFEMI/...`

### 用途範例
```bash
# 使用 Access Key 來執行 AWS CLI 命令
aws ec2 describe-instances    # 列出 EC2 實例
aws s3 ls                     # 列出 S3 buckets
aws sts get-caller-identity   # 查看目前身份
```

---

## 2️⃣ EC2 Key Pair（現在腳本在問的）

### 用途
- **用於 SSH 連線**：讓你從本機電腦 SSH 連線到 EC2 實例
- **類似密碼**：但比密碼更安全（使用公私鑰對）

### 設定位置
- 現在執行的 `setup-aws-key.sh` 就是在設定這個
- 儲存在：`~/.ssh/你的金鑰名稱.pem`

### 包含什麼
- **私鑰（Private Key）**：`.pem` 檔案，存在你的電腦
- **公鑰（Public Key）**：存在 AWS EC2，會自動加入實例

### 用途範例
```bash
# 使用 Key Pair 來 SSH 連線到 EC2
ssh -i ~/.ssh/my-ec2-key.pem ec2-user@1.2.3.4
```

---

## 📊 對照表

| 項目 | AWS CLI Access Key | EC2 Key Pair |
|------|-------------------|--------------|
| **用途** | API 認證 | SSH 連線 |
| **設定方式** | `aws configure` | `setup-aws-key.sh` 或 AWS Console |
| **儲存位置** | `~/.aws/credentials` | `~/.ssh/名稱.pem` |
| **包含內容** | Access Key ID + Secret | 私鑰檔案（.pem） |
| **使用時機** | 執行 AWS CLI 命令 | SSH 連線到 EC2 |
| **範例** | `aws ec2 describe-instances` | `ssh -i key.pem user@ip` |

---

## 🎯 現在的情況

### ✅ 已完成
- **AWS CLI Access Key**：已經透過 `aws configure` 設定完成
- 這讓你可以執行 AWS CLI 命令（例如列出 EC2 實例）

### 🔄 正在進行
- **EC2 Key Pair**：腳本正在詢問是否要建立新的 Key Pair
- 這是要用來 SSH 連線到 EC2 實例的

---

## 💡 為什麼需要 EC2 Key Pair？

### 情境：你想要 SSH 連線到 EC2 實例

```
你的電腦                    AWS EC2 實例
   │                           │
   │  SSH 連線                  │
   ├───────────────────────────>│
   │                           │
   │  需要 Key Pair 來認證      │
   │                           │
```

**沒有 Key Pair 的話：**
- ❌ 無法 SSH 連線到 EC2
- ❌ 無法在 EC2 上執行命令
- ❌ 無法設定 EC2 上的服務

**有 Key Pair 的話：**
- ✅ 可以安全地 SSH 連線
- ✅ 可以在 EC2 上執行命令
- ✅ 可以設定和管理 EC2

---

## 🚀 現在該怎麼做？

### 選項 1：建立新的 Key Pair（推薦）

如果你**還沒有** EC2 Key Pair，或想要建立一個新的：

```
要建立新的 Key Pair 嗎？(y/n): y
輸入 Key Pair 名稱（例如：my-ec2-key）: my-ec2-key
```

**腳本會：**
1. 在 AWS 建立新的 Key Pair
2. 下載私鑰到 `~/.ssh/my-ec2-key.pem`
3. 設定正確的權限（400）
4. 之後可以用這個 key 來 SSH 連線到 EC2

---

### 選項 2：使用現有的 Key Pair

如果你**已經有** EC2 Key Pair（例如之前建立的）：

```
要建立新的 Key Pair 嗎？(y/n): n
輸入要使用的 Key Pair 名稱: 你現有的-key-名稱
```

**前提：**
- Key Pair 已經在 AWS 存在
- 私鑰檔案已經下載到 `~/.ssh/` 目錄

---

## ⚠️ 重要提醒

### EC2 Key Pair 的安全性

1. **私鑰檔案（.pem）非常重要**
   - 不要分享給別人
   - 不要上傳到公開的地方（GitHub、雲端硬碟等）
   - 遺失後無法復原，需要重新建立

2. **權限設定**
   - 私鑰檔案必須設定為 `400` 或 `600` 權限
   - 腳本會自動設定，但請確認

3. **每個 EC2 實例**
   - 在建立 EC2 實例時，需要選擇一個 Key Pair
   - 之後只能用這個 Key Pair 來 SSH 連線

---

## 📝 完整流程

### 步驟 1：設定 AWS CLI Access Key（已完成 ✅）
```bash
aws configure
# 輸入 Access Key ID、Secret Access Key、Region、Output format
```

### 步驟 2：建立 EC2 Key Pair（正在進行 🔄）
```bash
./setup-aws-key.sh
# 選擇建立新的 Key Pair 或使用現有的
```

### 步驟 3：建立 EC2 實例時選擇 Key Pair
- 在 AWS Console 建立 EC2 時
- 選擇你剛才建立的 Key Pair

### 步驟 4：使用 Key Pair SSH 連線
```bash
ssh -i ~/.ssh/my-ec2-key.pem ec2-user@你的-EC2-IP
```

---

## ❓ 常見問題

### Q: 我還沒有 EC2 實例，需要現在建立 Key Pair 嗎？

**A:** 可以！建議先建立 Key Pair，之後建立 EC2 時就可以直接選擇使用。

### Q: 我可以建立多個 Key Pair 嗎？

**A:** 可以！每個 Key Pair 可以給不同的 EC2 實例使用，或給不同的使用者使用。

### Q: 如果我的私鑰檔案遺失了怎麼辦？

**A:** 無法復原。需要：
1. 建立新的 Key Pair
2. 重新建立 EC2 實例（選擇新的 Key Pair）
3. 或使用 AWS Systems Manager Session Manager（不需要 Key Pair）

### Q: 我已經有 EC2 實例了，但沒有 Key Pair 可以連線嗎？

**A:** 可以！使用 AWS Systems Manager Session Manager：
```bash
aws ssm start-session --target i-你的實例ID
```
不需要 Key Pair！

---

## 🎯 建議

**如果你還沒有 EC2 Key Pair：**
- 輸入 `y` 建立新的
- 輸入一個好記的名稱（例如：`my-ec2-key` 或 `macbook-ec2-key`）

**如果你已經有 EC2 Key Pair：**
- 輸入 `n` 使用現有的
- 輸入現有的 Key Pair 名稱

---

## 下一步

完成 Key Pair 設定後，腳本會：
1. 列出你的 EC2 實例
2. 讓你選擇要連線的實例
3. 測試 SSH 連線

繼續執行腳本即可！
