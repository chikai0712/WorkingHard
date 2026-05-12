#!/bin/bash

# 部署 Telegram 通知到現有的 Globalping EC2 實例

set -e

# 禁用代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY
unset socks_proxy SOCKS_PROXY socks5_proxy SOCKS5_PROXY
unset GIT_HTTP_PROXY GIT_HTTPS_PROXY

REGION="ap-northeast-1"
INSTANCE_ID="i-064d5f817958cf68e"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🚀 部署 Telegram 通知到 Globalping-V4.1-Tokyo..."
echo ""

# 獲取實例資訊
echo "📊 獲取實例資訊..."
INSTANCE_INFO=$(aws ec2 describe-instances \
    --region $REGION \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress,KeyName]' \
    --output text 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "❌ 無法連接 AWS"
    echo "請在系統終端執行此腳本"
    exit 1
fi

STATE=$(echo $INSTANCE_INFO | awk '{print $2}')
PUBLIC_IP=$(echo $INSTANCE_INFO | awk '{print $3}')
KEY_NAME=$(echo $INSTANCE_INFO | awk '{print $4}')

echo "  實例 ID: $INSTANCE_ID"
echo "  狀態: $STATE"
echo "  公網 IP: $PUBLIC_IP"
echo "  SSH Key: $KEY_NAME"
echo ""

# 如果實例停止，先啟動
if [ "$STATE" = "stopped" ]; then
    echo "⏳ 啟動實例..."
    aws ec2 start-instances --region $REGION --instance-ids $INSTANCE_ID
    aws ec2 wait instance-running --region $REGION --instance-ids $INSTANCE_ID
    
    PUBLIC_IP=$(aws ec2 describe-instances \
        --region $REGION \
        --instance-ids $INSTANCE_ID \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)
    
    echo "✅ 實例已啟動: $PUBLIC_IP"
    echo "⏳ 等待 SSH 就緒..."
    sleep 30
fi

# 測試 SSH 連線
echo "🔍 測試 SSH 連線..."
if ! ssh -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$PUBLIC_IP "echo 'SSH 連線成功'" 2>/dev/null; then
    echo "❌ SSH 連線失敗"
    echo ""
    echo "請檢查："
    echo "  1. SSH Key 是否存在: ls -la ~/.ssh/$KEY_NAME.pem"
    echo "  2. 安全組是否允許 SSH"
    echo "  3. 實例是否完全啟動"
    exit 1
fi

echo "✅ SSH 連線正常"
echo ""

# 檢查必要文件
echo "📋 檢查必要文件..."
REQUIRED_FILES=(
    "$PROJECT_DIR/GlobalpingChecker/telegram-config.env"
    "$PROJECT_DIR/GlobalpingChecker/telegram-notify.sh"
    "$PROJECT_DIR/GlobalpingChecker/id_globalping_multi_v3.3_Telegram.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 找不到文件: $file"
        exit 1
    fi
    echo "  ✓ $(basename $file)"
done

echo ""

# 檢查 EC2 上的目錄結構
echo "🔍 檢查 EC2 目錄結構..."
ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP << 'EOF'
# 檢查是否有 globalping-checker 目錄
if [ -d "/opt/globalping-checker" ]; then
    echo "  ✓ /opt/globalping-checker 目錄存在"
elif [ -d "$HOME/globalping-checker" ]; then
    echo "  ✓ $HOME/globalping-checker 目錄存在"
    echo "  → 將使用 $HOME/globalping-checker"
else
    echo "  ⚠️  未找到 globalping-checker 目錄"
    echo "  → 將創建 $HOME/globalping-checker"
    mkdir -p $HOME/globalping-checker
fi
EOF

echo ""

# 上傳文件
echo "📤 上傳 Telegram 配置和腳本..."

scp -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no \
    "$PROJECT_DIR/GlobalpingChecker/telegram-config.env" \
    ec2-user@$PUBLIC_IP:/tmp/

scp -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no \
    "$PROJECT_DIR/GlobalpingChecker/telegram-notify.sh" \
    ec2-user@$PUBLIC_IP:/tmp/

scp -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no \
    "$PROJECT_DIR/GlobalpingChecker/id_globalping_multi_v3.3_Telegram.sh" \
    ec2-user@$PUBLIC_IP:/tmp/

echo "✅ 文件已上傳"
echo ""

# 在 EC2 上配置
echo "🔧 配置 EC2..."
ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP << 'EOF'
# 確定目標目錄
if [ -d "/opt/globalping-checker" ]; then
    TARGET_DIR="/opt/globalping-checker"
    USE_SUDO="sudo"
else
    TARGET_DIR="$HOME/globalping-checker"
    USE_SUDO=""
fi

echo "  目標目錄: $TARGET_DIR"

# 移動文件
$USE_SUDO mv /tmp/telegram-config.env $TARGET_DIR/
$USE_SUDO mv /tmp/telegram-notify.sh $TARGET_DIR/
$USE_SUDO mv /tmp/id_globalping_multi_v3.3_Telegram.sh $TARGET_DIR/

# 設置權限
$USE_SUDO chmod +x $TARGET_DIR/*.sh
if [ -n "$USE_SUDO" ]; then
    $USE_SUDO chown ec2-user:ec2-user $TARGET_DIR/*
fi

echo "  ✓ 文件已配置"

# 檢查配置
if [ -f $TARGET_DIR/telegram-config.env ]; then
    echo "  ✓ Telegram 配置已安裝"
fi

# 列出目錄內容
echo ""
echo "  📁 $TARGET_DIR 內容："
ls -lh $TARGET_DIR/ | grep -E "telegram|v3.3"
EOF

echo "✅ EC2 配置完成"
echo ""

# 測試通知
echo "🧪 測試 Telegram 通知..."
echo ""
read -p "是否要執行測試檢測? (y/N): " TEST_CONFIRM

if [[ "$TEST_CONFIRM" =~ ^[Yy]$ ]]; then
    echo ""
    echo "執行測試檢測..."
    
    # 檢查是否有測試域名文件
    ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP << 'EOF'
# 確定目標目錄
if [ -d "/opt/globalping-checker" ]; then
    TARGET_DIR="/opt/globalping-checker"
else
    TARGET_DIR="$HOME/globalping-checker"
fi

# 創建測試域名文件
cat > $TARGET_DIR/test_domains.txt << 'TESTEOF'
google.com
facebook.com
TESTEOF

echo "執行測試..."
cd $TARGET_DIR
./id_globalping_multi_v3.3_Telegram.sh test_domains.txt
EOF
    
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
echo "  實例名稱: Globalping-V4.1-Tokyo"
echo "  公網 IP: $PUBLIC_IP"
echo "  Telegram 通知: 已啟用"
echo ""
echo "🔧 管理命令："
echo "  SSH 連線: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP"
echo "  執行檢測: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP 'cd ~/globalping-checker && ./id_globalping_multi_v3.3_Telegram.sh domains.txt'"
echo ""
echo "📝 下一步："
echo "  1. 上傳你的域名列表到 EC2"
echo "  2. 設置 cron 定時任務"
echo "  3. 執行檢測並接收 Telegram 通知"
echo ""
