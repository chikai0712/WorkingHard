# aws configure 操作說明

## 執行 aws configure 後的畫面

當你在終端機執行 `aws configure` 後，會看到以下互動式提示：

```
$ aws configure
AWS Access Key ID [None]: 
```

這表示命令正在等待你輸入。

---

## 完整操作流程

### 步驟 1：執行命令

```bash
aws configure
```

### 步驟 2：依序輸入（會逐行詢問）

#### 第 1 行：輸入 Access Key ID

```
AWS Access Key ID [None]: 
```

**操作：**
- 直接輸入你的 Access Key ID（例如：`AKIAIOSFODNN7EXAMPLE`）
- 輸入完後按 **Enter**

```
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
```

---

#### 第 2 行：輸入 Secret Access Key

```
AWS Secret Access Key [None]: 
```

**操作：**
- 輸入你的 Secret Access Key（例如：`wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`）
- ⚠️ **注意**：輸入時不會顯示任何字元（為了安全），這是正常的！
- 輸入完後按 **Enter**

```
AWS Secret Access Key [None]: 
（看起來像沒有輸入，但實際上已經輸入了）
```

---

#### 第 3 行：輸入預設區域

```
Default region name [None]: 
```

**操作：**
- 輸入 AWS 區域代碼，建議：
  - `ap-northeast-1`（東京，適合台灣）
  - `us-east-1`（維吉尼亞）
  - `us-west-2`（奧勒岡）
- 輸入完後按 **Enter**

```
Default region name [None]: ap-northeast-1
```

---

#### 第 4 行：輸入輸出格式

```
Default output format [None]: 
```

**操作：**
- 輸入輸出格式，建議：`json`
- 其他選項：`text`、`table`、`yaml`
- 輸入完後按 **Enter**

```
Default output format [None]: json
```

---

## 完整範例（實際操作）

```bash
$ aws configure
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name [None]: ap-northeast-1
Default output format [None]: json
```

**操作說明：**
1. 執行 `aws configure`
2. 看到 `AWS Access Key ID [None]:` → 輸入 Access Key ID → 按 Enter
3. 看到 `AWS Secret Access Key [None]:` → 輸入 Secret Access Key → 按 Enter（不會顯示）
4. 看到 `Default region name [None]:` → 輸入 `ap-northeast-1` → 按 Enter
5. 看到 `Default output format [None]:` → 輸入 `json` → 按 Enter
6. 完成！

---

## 視覺化說明

```
你的終端機畫面會是這樣：

ckchiu@RM03BY080 ~ % aws configure
AWS Access Key ID [None]: █
                          ↑
                    游標在這裡，等待你輸入
```

**輸入 Access Key ID 後：**

```
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: █
                               ↑
                         游標移到這裡，等待輸入 Secret
```

**輸入 Secret Access Key 時（不會顯示）：**

```
AWS Secret Access Key [None]: █
                               ↑
                    輸入時不會顯示任何字元（安全考量）
                    但實際上已經輸入了
```

---

## 重要提示

### ⚠️ Secret Access Key 輸入時不會顯示

這是**正常且安全的行為**！即使你看不到輸入的字元，實際上已經輸入了。

**不要擔心**，繼續輸入完整的 Secret Access Key，然後按 Enter。

### ✅ 如何確認輸入正確？

輸入完成後，執行：

```bash
aws sts get-caller-identity
```

如果成功顯示你的 AWS 帳號資訊，表示設定正確！

---

## 如果輸入錯誤怎麼辦？

### 方法 1：重新執行

```bash
aws configure
```

會覆蓋之前的設定。

### 方法 2：手動編輯

```bash
# 編輯憑證檔案
nano ~/.aws/credentials

# 或編輯配置檔案
nano ~/.aws/config
```

---

## 常見問題

### Q: 我已經在 "AWS Access Key ID [None]:" 這裡，要輸入什麼？

**A:** 
1. 前往 AWS Console → Security credentials
2. 建立 Access Key（如果還沒有）
3. 複製 Access Key ID
4. 在終端機貼上（Cmd+V 或 Ctrl+V）
5. 按 Enter

### Q: 輸入 Secret Access Key 時看不到字元？

**A:** 這是正常的！為了安全，終端機不會顯示密碼輸入。繼續輸入完整的 Secret Access Key，然後按 Enter。

### Q: 可以跳過某些欄位嗎？

**A:** 可以按 Enter 跳過，但建議都填寫：
- Access Key ID 和 Secret Access Key：**必須**（否則無法使用）
- Region：建議填寫（避免每次都要指定）
- Output format：建議填寫 `json`

### Q: 輸入時可以貼上嗎？

**A:** 可以！使用：
- macOS: `Cmd + V`
- Linux/Windows: `Ctrl + Shift + V` 或 `Ctrl + V`

---

## 快速檢查

設定完成後，測試：

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

如果成功，表示設定完成！

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
