# 網站切換部署系統

這個系統讓你可以快速在兩套網站之間切換並部署到 AWS EC2 服務器。

## 📁 目錄結構

```
Project/
├── websites/
│   ├── site1-test/          # 第一套：DNS 測試頁面
│   │   ├── aws.html         # AWS 藍色頁面
│   │   └── google.html      # Google 紅色頁面
│   └── site2-gaming/        # 第二套：博弈網站
│       ├── aws.html         # AWS 博弈頁面
│       └── google.html      # Google 博弈頁面
└── scripts/
    └── deploy-website.sh    # 部署切換腳本
```

## 🚀 快速開始

### 1. 準備 SSH 密鑰

**方式一：自動檢測（推薦）**

只需將你的 `.pem` 文件放在 `~/.ssh/` 目錄中，腳本會自動檢測：

```bash
# 複製密鑰到 ~/.ssh/ 目錄
cp /path/to/your-key.pem ~/.ssh/

# 腳本會自動檢測並使用
```

**方式二：手動指定**

編輯 `scripts/deploy-website.sh`，修改以下配置：

```bash
EC2_KEY="~/.ssh/your-key.pem"   # 指定密鑰路徑
EC2_USER="ec2-user"             # 指定用戶名（可選，留空自動檢測）
```

### 2. 部署網站

```bash
cd /Users/ckchiu/Desktop/Project

# 部署測試網站（藍色 AWS + 紅色 Google）
bash scripts/deploy-website.sh 1

# 部署博弈網站（皇冠娛樂城）
bash scripts/deploy-website.sh 2
```

### 3. 查看部署狀態

```bash
bash scripts/deploy-website.sh status
```

## 📋 網站說明

### 網站 1：DNS 測試頁面
- **用途**：測試 DNS failover 功能
- **AWS 頁面**：藍色背景，顯示「我是 AWS」
- **Google 頁面**：紅色背景，顯示「我是 Google」
- **特點**：簡潔明瞭，方便測試

### 網站 2：博弈網站
- **用途**：皇冠娛樂城
- **AWS 頁面**：藍色徽章，顯示 AWS 主服務器
- **Google 頁面**：紅色徽章，顯示 Google 備援服務器
- **特點**：完整的博弈網站界面，包含多種遊戲

## 🔧 部署流程

當你執行部署命令時，腳本會：

1. ✅ 自動檢測 SSH 密鑰（或使用指定的密鑰）
2. ✅ 自動檢測 EC2 用戶名（ec2-user, ubuntu, admin）
3. ✅ 檢查並修正密鑰權限（設為 400）
4. ✅ 檢查 SSH 連線
5. ✅ 備份現有網站
6. ✅ 上傳新網站文件
7. ✅ 設置文件權限
8. ✅ 重啟 Web 服務
9. ✅ 顯示部署結果

## 🎯 使用場景

### 場景 1：測試 DNS Failover

```bash
# 1. 部署測試網站
bash scripts/deploy-website.sh 1

# 2. 執行 DNS failover 測試
cd bind-dns-local
sudo bash scripts/dns-failover-test.sh

# 3. 觀察網站切換（藍色 ↔ 紅色）
```

### 場景 2：上線博弈網站

```bash
# 切換到博弈網站
bash scripts/deploy-website.sh 2

# 確認部署狀態
bash scripts/deploy-website.sh status

# 訪問網站
open http://www.clouddeployment168.site
```

### 場景 3：快速回滾

```bash
# 如果博弈網站有問題，快速切回測試網站
bash scripts/deploy-website.sh 1
```

## 🌐 訪問網址

部署完成後，可以通過以下方式訪問：

- **直接 IP**：
  - http://35.74.79.10
  - http://35.78.244.92

- **域名**（透過 DNS）：
  - http://www.clouddeployment168.site

## 🛠️ 自定義網站

### 修改測試網站

編輯以下文件：
- `websites/site1-test/aws.html`
- `websites/site1-test/google.html`

### 修改博弈網站

編輯以下文件：
- `websites/site2-gaming/aws.html`
- `websites/site2-gaming/google.html`

### 添加新網站

1. 創建新目錄：`websites/site3-xxx/`
2. 添加 `aws.html` 和 `google.html`
3. 修改 `scripts/deploy-website.sh`，添加新的 case

## 📊 部署服務器

| 服務器 | IP | 用途 | 部署文件 |
|--------|-----|------|---------|
| AWS Server 1 | 35.74.79.10 | 主服務器 | aws.html |
| AWS Server 2 | 35.78.244.92 | 主服務器 | aws.html |

**注意**：兩台 AWS 服務器都部署相同的 `aws.html` 文件。

## 🔐 安全注意事項

1. **SSH 密鑰權限**：腳本會自動設置為 400
   ```bash
   # 手動設置（如果需要）
   chmod 400 ~/.ssh/your-key.pem
   ```

2. **自動檢測功能**：
   - 自動搜尋 `~/.ssh/*.pem` 文件
   - 自動嘗試常見用戶名（ec2-user, ubuntu, admin）
   - 如果找到多個密鑰，會提示選擇

3. **備份**：腳本會自動備份現有網站到 `index.html.backup.YYYYMMDD_HHMMSS`

4. **確認提示**：部署前會要求確認，避免誤操作

## 🐛 故障排除

### 問題 1：找不到 SSH 密鑰

**解決方法：**

```bash
# 方法 1：將密鑰複製到 ~/.ssh/ 目錄
cp /path/to/your-key.pem ~/.ssh/

# 方法 2：在腳本中手動指定
# 編輯 scripts/deploy-website.sh
EC2_KEY="/path/to/your-key.pem"
```

### 問題 2：SSH 連線失敗

**可能原因：**
- 密鑰權限不正確（腳本會自動修正）
- EC2 Security Group 未開放 SSH（22 埠）
- 密鑰與 EC2 實例不匹配

**檢查方法：**

```bash
# 手動測試連線（腳本會自動檢測用戶名）
ssh -i ~/.ssh/your-key.pem ec2-user@35.74.79.10

# 檢查 AWS Security Group
# 確保入站規則包含：SSH (22) from 0.0.0.0/0 或你的 IP
```

### 問題 3：自動檢測到多個密鑰

腳本會列出所有找到的 `.pem` 文件，並提示你選擇：

```
找到多個密鑰文件：
  1) my-key-1.pem
  2) my-key-2.pem
  3) my-key-3.pem

請選擇密鑰編號 [1-3]: 
```

輸入對應的編號即可。

### 問題 4：網站無法訪問

```bash
# 檢查 Web 服務狀態
ssh -i ~/.ssh/your-key.pem ec2-user@35.74.79.10 "sudo systemctl status httpd"

# 檢查 AWS Security Group
# 確保入站規則包含：HTTP (80) from 0.0.0.0/0

# 檢查防火牆
ssh -i ~/.ssh/your-key.pem ec2-user@35.74.79.10 "sudo firewall-cmd --list-all"
```

### 問題 5：文件上傳失敗

```bash
# 檢查磁碟空間
ssh -i ~/.ssh/your-key.pem ec2-user@35.74.79.10 "df -h"

# 檢查目錄權限
ssh -i ~/.ssh/your-key.pem ec2-user@35.74.79.10 "ls -la /var/www/html"
```

## 📝 更新日誌

- **v1.0** (2025-02-05)
  - ✅ 初始版本
  - ✅ 支援兩套網站切換
  - ✅ 自動備份功能
  - ✅ 部署狀態檢查

## 💡 提示

- 部署前建議先執行 `status` 檢查當前狀態
- 每次部署都會自動備份，可以安心操作
- 如果只想更新單台服務器，可以修改腳本註釋掉另一台
- 建議在測試環境先驗證網站，再部署到生產環境
