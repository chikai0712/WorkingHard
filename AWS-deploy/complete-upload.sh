#!/bin/bash

# 完整的文件上傳和配置腳本
# 請在系統終端執行

echo "🚀 Globalping Checker 完整部署到 EC2"
echo "========================================"
echo ""

# 配置
IP="54.238.247.106"
INSTANCE_ID="i-064d5f817958cf68e"
REGION="ap-northeast-1"

# 步驟 1：查詢實例使用的密鑰
echo "步驟 1：查詢實例密鑰..."
KEY_NAME=$(aws ec2 describe-instances \
    --region $REGION \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].KeyName' \
    --output text)

if [ -z "$KEY_NAME" ] || [ "$KEY_NAME" = "None" ]; then
    echo "❌ 無法查詢密鑰名稱"
    echo ""
    echo "請手動指定密鑰："
    echo "  export KEY_NAME='your-key-name'"
    echo "  然後重新執行此腳本"
    exit 1
fi

echo "✅ 實例使用的密鑰: $KEY_NAME"
KEY_FILE="$HOME/.ssh/${KEY_NAME}.pem"

if [ ! -f "$KEY_FILE" ]; then
    echo "❌ 找不到密鑰文件: $KEY_FILE"
    echo ""
    echo "可用的密鑰："
    ls -1 ~/.ssh/*.pem
    exit 1
fi

echo "✅ 找到密鑰文件: $KEY_FILE"
echo ""

# 步驟 2：測試 SSH 連線
echo "步驟 2：測試 SSH 連線..."
if ! ssh -i "$KEY_FILE" -o ConnectTimeout=10 -o StrictHostKeyChecking=no \
    ec2-user@$IP "echo 'SSH 連線成功'" 2>/dev/null; then
    echo "❌ SSH 連線失敗"
    echo ""
    echo "請檢查："
    echo "  1. 實例是否正在運行"
    echo "  2. 安全組是否允許你的 IP 訪問 SSH (端口 22)"
    echo "  3. 密鑰權限: chmod 400 $KEY_FILE"
    exit 1
fi

echo "✅ SSH 連線正常"
echo ""

# 步驟 3：上傳文件
echo "步驟 3：上傳文件..."
cd ~/Desktop/Project/GlobalpingChecker

FILES=(
    "smart-check.sh"
    "auto-quota-check.sh"
    "telegram-config.env"
    "telegram-notify.sh"
    "id_globalping_multi_v3.3_Telegram.sh"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  上傳: $file"
        scp -i "$KEY_FILE" -o StrictHostKeyChecking=no "$file" ec2-user@$IP:~/
    else
        echo "  ⚠️  找不到: $file"
    fi
done

echo "✅ 文件上傳完成"
echo ""

# 步驟 4：配置 EC2
echo "步驟 4：配置 EC2 環境..."
ssh -i "$KEY_FILE" ec2-user@$IP << 'EOF'
# 創建目錄
mkdir -p ~/globalping-checker

# 移動文件
mv ~/*.sh ~/globalping-checker/ 2>/dev/null
mv ~/telegram-*.* ~/globalping-checker/ 2>/dev/null

# 設置權限
cd ~/globalping-checker
chmod +x *.sh

echo "✓ 文件已配置"

# 列出文件
echo ""
echo "📁 ~/globalping-checker 內容："
ls -lh ~/globalping-checker/
EOF

echo "✅ EC2 配置完成"
echo ""

# 步驟 5：設置 cron
echo "步驟 5：設置定時任務..."
echo ""
echo "請執行以下命令設置 cron："
echo ""
echo "  ssh -i $KEY_FILE ec2-user@$IP"
echo "  crontab -e"
echo ""
echo "添加以下行："
echo "  */10 * * * * cd ~/globalping-checker && bash smart-check.sh domains.txt >> ~/smart-check.log 2>&1"
echo ""

# 步驟 6：測試
echo "步驟 6：測試檢測..."
read -p "是否要執行測試檢測? (y/N): " TEST

if [[ "$TEST" =~ ^[Yy]$ ]]; then
    echo ""
    echo "執行測試..."
    ssh -i "$KEY_FILE" ec2-user@$IP "cd ~/globalping-checker && bash smart-check.sh domains.txt"
    echo ""
    echo "✅ 測試完成！請檢查 Telegram 是否收到通知"
fi

echo ""
echo "========================================"
echo "🎉 部署完成！"
echo "========================================"
echo ""
echo "📊 配置資訊："
echo "  實例 ID: $INSTANCE_ID"
echo "  公網 IP: $IP"
echo "  SSH Key: $KEY_NAME"
echo ""
echo "🔧 管理命令："
echo "  SSH 連線: ssh -i $KEY_FILE ec2-user@$IP"
echo "  查看日誌: ssh -i $KEY_FILE ec2-user@$IP 'tail -f ~/smart-check.log'"
echo "  手動檢測: ssh -i $KEY_FILE ec2-user@$IP 'cd ~/globalping-checker && bash smart-check.sh domains.txt'"
echo ""
