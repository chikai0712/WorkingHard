# GlobalpingChecker V4.1 - AWS 部署指南

## 🚀 快速部署

### 方法 1：一鍵部署（推薦）

在**系統終端**（Terminal.app）中執行：

```bash
cd /Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1
chmod +x deploy-to-aws.sh
./deploy-to-aws.sh
```

### 方法 2：手動部署

如果自動部署失敗，可以手動執行以下步驟。

## 📋 部署前準備

### 1. 檢查 SSH 連接

```bash
ssh -i ~/.ssh/globalping-checker-key.pem ubuntu@54.238.247.106
```

如果 `ubuntu` 用戶無法連接，嘗試 `ec2-user`：

```bash
ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@54.238.247.106
```

### 2. 確認 .env 配置

確保 `/Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1/.env` 包含：

```env
# Globalping API Token
GLOBALPING_TOKEN=uh5vlg4ttg3v5gwby5zgtqrciimahql5

# 檢測間隔（分鐘）
CHECK_INTERVAL_MINUTES=90

# 異常區檢測時間（小時，24小時制）
ABNORMAL_CHECK_HOUR=1

# 正常區檢測時間（小時，24小時制）
NORMAL_CHECK_HOUR=9

# 最大迭代次數（異常區）
MAX_ITERATIONS=10
```

## 🔧 手動部署步驟

### 步驟 1：打包代碼

```bash
cd /Users/ckchiu/Desktop/Project/GlobalpingChecker
tar -czf v4.1-deploy.tar.gz \
    --exclude='v4.1/__pycache__' \
    --exclude='v4.1/app/__pycache__' \
    --exclude='v4.1/venv' \
    v4.1/
```

### 步驟 2：上傳到 AWS

```bash
# 使用 ubuntu 用戶
scp -i ~/.ssh/globalping-checker-key.pem v4.1-deploy.tar.gz ubuntu@54.238.247.106:~/

# 或使用 ec2-user
scp -i ~/.ssh/globalping-checker-key.pem v4.1-deploy.tar.gz ec2-user@54.238.247.106:~/
```

### 步驟 3：SSH 登入 AWS

```bash
ssh -i ~/.ssh/globalping-checker-key.pem ubuntu@54.238.247.106
# 或
ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@54.238.247.106
```

### 步驟 4：在 AWS 上部署

```bash
# 停止舊服務
cd ~/globalping-v4.1 2>/dev/null && docker-compose down || true

# 備份舊版本
cd ~
if [ -d "globalping-v4.1" ]; then
    mv globalping-v4.1 globalping-v4.1-backup-$(date +%Y%m%d-%H%M%S)
fi

# 解壓新版本
tar -xzf v4.1-deploy.tar.gz
mv v4.1 globalping-v4.1
cd globalping-v4.1

# 確保數據目錄權限
chmod 777 data
chmod 666 data/globalping_results.db 2>/dev/null || true

# 啟動服務
docker-compose up -d --build

# 查看日誌
docker-compose logs -f
```

## 📊 驗證部署

### 1. 檢查服務狀態

```bash
cd ~/globalping-v4.1
docker-compose ps
```

應該看到 `globalping_v41_web` 服務在運行。

### 2. 測試 API

在本地終端執行：

```bash
curl http://54.238.247.106:8000/api/stats
```

### 3. 訪問 Dashboard

在瀏覽器中打開：

**http://54.238.247.106:8000**

## 🔍 故障排除

### 問題 1：無法連接 SSH

**解決方案：**
1. 檢查 SSH 密鑰權限：`chmod 400 ~/.ssh/globalping-checker-key.pem`
2. 檢查 AWS 安全組是否允許 SSH（端口 22）
3. 確認 IP 地址是否正確

### 問題 2：端口 8000 無法訪問

**解決方案：**
1. 檢查 AWS 安全組是否允許入站流量（端口 8000）
2. 檢查容器是否正在運行：`docker-compose ps`
3. 查看日誌：`docker-compose logs`

### 問題 3：數據庫權限錯誤

**解決方案：**
```bash
cd ~/globalping-v4.1
chmod 777 data
chmod 666 data/globalping_results.db
docker-compose restart
```

### 問題 4：服務無法啟動

**解決方案：**
```bash
cd ~/globalping-v4.1

# 查看詳細日誌
docker-compose logs

# 重新構建
docker-compose down
docker-compose up -d --build

# 如果還是失敗，檢查 .env 文件
cat .env
```

## 🛠️ 常用管理命令

### 查看日誌

```bash
cd ~/globalping-v4.1
docker-compose logs -f
```

### 重啟服務

```bash
cd ~/globalping-v4.1
docker-compose restart
```

### 停止服務

```bash
cd ~/globalping-v4.1
docker-compose down
```

### 更新域名列表

```bash
# 在本地編輯 domains.txt
# 然後上傳
scp -i ~/.ssh/globalping-checker-key.pem domains.txt ubuntu@54.238.247.106:~/globalping-v4.1/

# SSH 登入並重啟
ssh -i ~/.ssh/globalping-checker-key.pem ubuntu@54.238.247.106
cd ~/globalping-v4.1
docker-compose restart
```

### 備份數據庫

```bash
# SSH 登入
ssh -i ~/.ssh/globalping-checker-key.pem ubuntu@54.238.247.106

# 備份數據庫
cd ~/globalping-v4.1
cp data/globalping_results.db data/globalping_results.db.backup-$(date +%Y%m%d-%H%M%S)

# 下載到本地
exit
scp -i ~/.ssh/globalping-checker-key.pem ubuntu@54.238.247.106:~/globalping-v4.1/data/globalping_results.db ./
```

## 📈 監控和維護

### 檢查系統資源

```bash
# SSH 登入
ssh -i ~/.ssh/globalping-checker-key.pem ubuntu@54.238.247.106

# 查看磁盤使用
df -h

# 查看內存使用
free -h

# 查看 Docker 容器資源
docker stats
```

### 清理舊備份

```bash
# 列出備份
ls -lh ~/globalping-v4.1-backup-*

# 刪除舊備份（保留最近 3 個）
ls -t ~/globalping-v4.1-backup-* | tail -n +4 | xargs rm -rf
```

## 🔐 安全建議

1. **定期更新 API Token**
   - 在 Globalping 網站更新 token
   - 更新 `.env` 文件
   - 重啟服務

2. **限制訪問 IP**
   - 在 AWS 安全組中限制允許訪問的 IP 地址

3. **定期備份數據庫**
   - 建議每天備份一次
   - 保留最近 7 天的備份

4. **監控日誌**
   - 定期檢查錯誤日誌
   - 設置告警通知

## 📞 技術支持

如果遇到問題：

1. 查看日誌：`docker-compose logs`
2. 檢查服務狀態：`docker-compose ps`
3. 測試 API：`curl http://54.238.247.106:8000/api/stats`
4. 查看數據庫：`sqlite3 data/globalping_results.db "SELECT COUNT(*) FROM domains;"`

## 🎯 部署檢查清單

- [ ] SSH 連接正常
- [ ] .env 文件配置正確
- [ ] 代碼已打包上傳
- [ ] 舊服務已停止
- [ ] 新服務已啟動
- [ ] API 響應正常
- [ ] Dashboard 可訪問
- [ ] 數據庫權限正確
- [ ] 日誌無錯誤
- [ ] 安全組配置正確

## 📝 版本信息

- **版本**: V4.1 (SQLite)
- **數據庫**: SQLite（無需 PostgreSQL）
- **時區**: GMT+8 (Asia/Taipei)
- **檢測間隔**: 90 分鐘
- **循環切換**: AM 1:00 / AM 9:00
