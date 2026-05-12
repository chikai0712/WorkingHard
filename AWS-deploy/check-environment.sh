#!/bin/bash

# AWS 部署前置檢查和修復腳本

echo "🔍 AWS 部署環境檢查..."
echo ""

# 1. 禁用代理
echo "1. 禁用代理設置..."
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY
unset socks_proxy SOCKS_PROXY

# 檢查是否還有代理環境變數
if [ -n "$http_proxy" ] || [ -n "$https_proxy" ]; then
    echo "  ⚠️  代理仍然啟用，請手動執行："
    echo "     unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY"
else
    echo "  ✅ 代理已禁用"
fi

echo ""

# 2. 測試 AWS CLI
echo "2. 測試 AWS CLI 連線..."
if aws sts get-caller-identity --no-cli-pager 2>/dev/null; then
    echo "  ✅ AWS CLI 連線正常"
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    USER_ARN=$(aws sts get-caller-identity --query Arn --output text)
    
    echo "  帳號 ID: $ACCOUNT_ID"
    echo "  用戶: $USER_ARN"
else
    echo "  ❌ AWS CLI 連線失敗"
    echo ""
    echo "  可能的原因："
    echo "    1. AWS 憑證未配置"
    echo "    2. 代理設置問題"
    echo "    3. 網路連線問題"
    echo ""
    echo "  解決方法："
    echo "    1. 執行: aws configure"
    echo "    2. 確認代理已禁用: env | grep -i proxy"
    echo "    3. 測試網路: ping aws.amazon.com"
    exit 1
fi

echo ""

# 3. 檢查 EC2 實例
echo "3. 檢查現有 EC2 實例..."
INSTANCES=$(aws ec2 describe-instances \
    --region ap-northeast-1 \
    --query 'Reservations[].Instances[].[InstanceId,State.Name,Tags[?Key==`Name`].Value|[0]]' \
    --output text 2>/dev/null)

if [ -z "$INSTANCES" ]; then
    echo "  ℹ️  沒有 EC2 實例"
else
    echo "$INSTANCES" | while read INSTANCE_ID STATE NAME; do
        echo "  - $NAME: $STATE ($INSTANCE_ID)"
    done
fi

echo ""

# 4. 檢查 SSH 密鑰
echo "4. 檢查 SSH 密鑰..."
for KEY in pokemon-game-key globalping-checker-key dns-monitoring-key; do
    if [ -f ~/.ssh/$KEY.pem ]; then
        PERMS=$(stat -f "%Lp" ~/.ssh/$KEY.pem 2>/dev/null || stat -c "%a" ~/.ssh/$KEY.pem 2>/dev/null)
        if [ "$PERMS" = "400" ]; then
            echo "  ✅ $KEY.pem (權限: $PERMS)"
        else
            echo "  ⚠️  $KEY.pem (權限: $PERMS，應為 400)"
            chmod 400 ~/.ssh/$KEY.pem
            echo "     已修正為 400"
        fi
    else
        echo "  ℹ️  $KEY.pem (未創建)"
    fi
done

echo ""

# 5. 檢查安全組
echo "5. 檢查安全組..."
SECURITY_GROUPS=$(aws ec2 describe-security-groups \
    --region ap-northeast-1 \
    --filters "Name=group-name,Values=*-sg" \
    --query 'SecurityGroups[].[GroupName,GroupId]' \
    --output text 2>/dev/null)

if [ -z "$SECURITY_GROUPS" ]; then
    echo "  ℹ️  沒有安全組"
else
    echo "$SECURITY_GROUPS" | while read NAME GROUP_ID; do
        echo "  - $NAME ($GROUP_ID)"
    done
fi

echo ""
echo "=========================================="
echo "✅ 環境檢查完成"
echo "=========================================="
echo ""
echo "💡 下一步："
echo "  1. 如果所有檢查都通過，可以開始部署"
echo "  2. 執行: ./aws-manager.sh"
echo ""
echo "⚠️  重要提醒："
echo "  - 確保在執行部署前代理已禁用"
echo "  - 建議在新的終端視窗執行部署腳本"
echo ""
