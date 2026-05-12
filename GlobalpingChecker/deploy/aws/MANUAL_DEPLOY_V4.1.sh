#!/bin/bash

# ============================================
# V4.1 手動部署指南
# 請在系統終端（Terminal.app）執行此腳本
# ============================================

cat << 'EOF'

🚀 V4.1 手動部署到 AWS

由於 Cursor 環境的網路限制，請按照以下步驟在系統終端執行：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 步驟 1：打開系統終端

1. 按 Cmd+Space 打開 Spotlight
2. 輸入 "Terminal" 並打開
3. 或使用 iTerm（如果已安裝）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 步驟 2：在終端執行以下命令

# 1. 禁用代理
export http_proxy=""
export https_proxy=""
export HTTP_PROXY=""
export HTTPS_PROXY=""
export all_proxy=""
export ALL_PROXY=""
export no_proxy="*"
export NO_PROXY="*"

# 2. 進入項目目錄
cd ~/Desktop/Project/GlobalpingChecker

# 3. 確認打包文件存在
ls -lh v4.1-update.tar.gz

# 4. 測試 SSH 連線
ssh -i ~/.ssh/globalping-checker-key.pem ubuntu@54.238.247.106 "echo 'SSH 連線成功'"

# 如果上面顯示 "SSH 連線成功"，繼續執行：

# 5. 上傳文件到 AWS
scp -i ~/.ssh/globalping-checker-key.pem v4.1-update.tar.gz ubuntu@54.238.247.106:~/

# 6. SSH 到 AWS
ssh -i ~/.ssh/globalping-checker-key.pem ubuntu@54.238.247.106

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 步驟 3：在 AWS 上執行部署（SSH 連線後）

# 停止當前服務
cd ~/v4.1
docker-compose down

# 備份配置
cp .env /tmp/v4.1.env.backup
cp domains.txt /tmp/v4.1.domains.backup

# 備份舊版本
cd ~
mv v4.1 v4.1-backup-$(date +%Y%m%d-%H%M%S)

# 解壓新版本
tar -xzf v4.1-update.tar.gz
cd v4.1

# 恢復配置
cp /tmp/v4.1.env.backup .env
cp /tmp/v4.1.domains.backup domains.txt

# 啟動服務
docker-compose up -d --build

# 查看日誌（按 Ctrl+C 退出）
docker-compose logs -f --tail=50

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 步驟 4：驗證部署（在本地終端執行）

# 測試 API
curl http://54.238.247.106:8000/api/stats | python3 -m json.tool

# 訪問 Dashboard
open http://54.238.247.106:8000

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 如果 SSH 連線失敗

1. 檢查實例狀態（在終端執行）：
   aws ec2 describe-instances \
       --region ap-northeast-1 \
       --filters "Name=tag:Name,Values=Globalping-V4.1-Tokyo" \
       --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress]' \
       --output table

2. 如果實例停止，啟動它：
   aws ec2 start-instances --region ap-northeast-1 --instance-ids <INSTANCE_ID>
   
3. 等待 2-3 分鐘後重試 SSH

4. 檢查安全組是否允許 SSH (port 22)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 部署完成後的管理命令

# SSH 連線
ssh -i ~/.ssh/globalping-checker-key.pem ubuntu@54.238.247.106

# 查看服務狀態
cd v4.1 && docker-compose ps

# 查看日誌
cd v4.1 && docker-compose logs -f --tail=50

# 重啟服務
cd v4.1 && docker-compose restart

# 停止服務
cd v4.1 && docker-compose down

# 啟動服務
cd v4.1 && docker-compose up -d

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 更新內容

1. API_ERROR 處理
   - 遇到 HTTP 429/500+ 時自動等待 60 分鐘
   - 記錄暫停和恢復時間

2. 時區設置
   - 系統時區：GMT+8 (Asia/Taipei)
   - PostgreSQL 時區：GMT+8
   - 檢測時間：AM 1:00 (異常區), AM 9:00 (正常區)

3. 智能循環檢測
   - 自動區域管理（正常區、異常區、待分類）
   - 每 90 分鐘檢測一次
   - 最多 10 次迭代

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 提示

- 所有命令都需要在系統終端執行，不要在 Cursor 內執行
- 確保已禁用代理
- 如果遇到問題，請提供錯誤訊息

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF
