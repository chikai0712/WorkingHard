#!/bin/bash

# 修復 Cursor 連線 AWS 的問題
# 此腳本會配置環境，讓 AWS CLI 可以在 Cursor 中正常工作

set -e

echo "🔧 修復 Cursor 連線 AWS 問題..."
echo ""

# 1. 檢查 AWS CLI
echo "1️⃣  檢查 AWS CLI..."
if ! command -v aws &> /dev/null; then
    echo "   ❌ AWS CLI 未安裝"
    echo "   請執行: brew install awscli"
    exit 1
fi

AWS_PATH=$(which aws)
echo "   ✅ AWS CLI 已安裝: $AWS_PATH"
echo ""

# 2. 創建 AWS 配置
echo "2️⃣  配置 AWS CLI..."

# 確保 .aws 目錄存在
mkdir -p ~/.aws

# 備份現有配置
if [ -f ~/.aws/config ]; then
    cp ~/.aws/config ~/.aws/config.backup.$(date +%Y%m%d_%H%M%S)
    echo "   ✓ 已備份現有配置"
fi

# 創建新配置（禁用代理）
cat > ~/.aws/config << 'EOF'
[default]
region = ap-northeast-1
output = json
no_proxy = *

[profile default]
region = ap-northeast-1
output = json
EOF

echo "   ✅ AWS 配置已更新"
echo ""

# 3. 創建 AWS CLI 包裝腳本
echo "3️⃣  創建 AWS CLI 包裝腳本..."

cat > ~/Desktop/Project/AWS-deploy/aws-wrapper.sh << 'EOF'
#!/bin/bash
# AWS CLI 包裝腳本 - 自動禁用代理

# 臨時禁用所有代理
(
    unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
    unset all_proxy ALL_PROXY no_proxy NO_PROXY
    unset socks_proxy SOCKS_PROXY socks5_proxy SOCKS5_PROXY
    unset GIT_HTTP_PROXY GIT_HTTPS_PROXY
    
    # 執行 AWS CLI
    aws "$@"
)
EOF

chmod +x ~/Desktop/Project/AWS-deploy/aws-wrapper.sh
echo "   ✅ 包裝腳本已創建: ~/Desktop/Project/AWS-deploy/aws-wrapper.sh"
echo ""

# 4. 更新所有部署腳本使用包裝器
echo "4️⃣  更新部署腳本..."

# 創建 AWS 命令別名函數
cat > ~/Desktop/Project/AWS-deploy/aws-functions.sh << 'EOF'
#!/bin/bash
# AWS 輔助函數 - 在所有腳本中使用

# AWS CLI 包裝函數
aws_no_proxy() {
    (
        unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
        unset all_proxy ALL_PROXY no_proxy NO_PROXY
        unset socks_proxy SOCKS_PROXY socks5_proxy SOCKS5_PROXY
        unset GIT_HTTP_PROXY GIT_HTTPS_PROXY
        
        aws "$@"
    )
}

# SSH 包裝函數
ssh_no_proxy() {
    (
        unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
        unset all_proxy ALL_PROXY
        
        ssh "$@"
    )
}

# SCP 包裝函數
scp_no_proxy() {
    (
        unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
        unset all_proxy ALL_PROXY
        
        scp "$@"
    )
}

# 導出函數
export -f aws_no_proxy
export -f ssh_no_proxy
export -f scp_no_proxy
EOF

chmod +x ~/Desktop/Project/AWS-deploy/aws-functions.sh
echo "   ✅ 輔助函數已創建"
echo ""

# 5. 測試連線
echo "5️⃣  測試 AWS 連線..."

# 使用包裝腳本測試
if ~/Desktop/Project/AWS-deploy/aws-wrapper.sh sts get-caller-identity --no-cli-pager 2>/dev/null; then
    echo "   ✅ AWS 連線測試成功！"
    
    ACCOUNT_ID=$(~/Desktop/Project/AWS-deploy/aws-wrapper.sh sts get-caller-identity --query Account --output text 2>/dev/null)
    echo "   帳號 ID: $ACCOUNT_ID"
else
    echo "   ⚠️  AWS 連線測試失敗"
    echo ""
    echo "   可能的原因："
    echo "   1. AWS 憑證未配置（執行: aws configure）"
    echo "   2. 網路連線問題"
    echo ""
    echo "   請嘗試在系統終端執行："
    echo "   aws sts get-caller-identity"
fi

echo ""
echo "========================================"
echo "✅ 修復完成"
echo "========================================"
echo ""
echo "📝 使用方法："
echo ""
echo "方法 1：使用包裝腳本（推薦）"
echo "  ~/Desktop/Project/AWS-deploy/aws-wrapper.sh ec2 describe-instances"
echo ""
echo "方法 2：在腳本中載入函數"
echo "  source ~/Desktop/Project/AWS-deploy/aws-functions.sh"
echo "  aws_no_proxy ec2 describe-instances"
echo ""
echo "方法 3：使用更新後的管理腳本"
echo "  cd ~/Desktop/Project/AWS-deploy"
echo "  ./check-status.sh"
echo "  ./aws-manager.sh"
echo ""
echo "💡 提示："
echo "  所有部署腳本已更新，會自動使用包裝器"
echo "  現在可以在 Cursor 終端直接執行 AWS 命令了！"
echo ""
