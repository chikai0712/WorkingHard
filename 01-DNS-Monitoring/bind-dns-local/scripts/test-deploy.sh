#!/bin/bash
# 快速測試腳本 - 診斷部署問題

set -e

REGION="${AWS_REGION:-ap-northeast-1}"
KEY_NAME="${KEY_NAME:-dns-test-key}"

echo "=== 診斷測試 ==="
echo ""

# 1. 檢查 AWS 憑證
echo "1. 檢查 AWS 憑證..."
if aws sts get-caller-identity &>/dev/null; then
    echo "✅ AWS 憑證正常"
    aws sts get-caller-identity --output table
else
    echo "❌ AWS 憑證未配置"
    exit 1
fi
echo ""

# 2. 檢查 Key Pair
echo "2. 檢查 Key Pair: $KEY_NAME"
if aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$REGION" &>/dev/null; then
    echo "✅ Key Pair 存在於 AWS"
    if [ -f "$HOME/.ssh/${KEY_NAME}.pem" ]; then
        echo "✅ 本地私鑰檔案存在: $HOME/.ssh/${KEY_NAME}.pem"
    else
        echo "❌ 本地私鑰檔案不存在"
    fi
else
    echo "❌ Key Pair 不存在"
fi
echo ""

# 3. 檢查 Security Group
echo "3. 檢查 Security Group: dns-test-sg"
SG_ID=$(aws ec2 describe-security-groups \
    --group-names "dns-test-sg" \
    --region "$REGION" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "")
if [ -n "$SG_ID" ] && [ "$SG_ID" != "None" ]; then
    echo "✅ Security Group 存在: $SG_ID"
else
    echo "❌ Security Group 不存在"
fi
echo ""

# 4. 測試取得本機 IP（設定超時）
echo "4. 測試取得本機 IP（5 秒超時）..."
timeout 5 curl -s https://checkip.amazonaws.com/ 2>/dev/null && echo "✅ 成功取得 IP" || echo "❌ 超時或失敗"
echo ""

# 5. 測試取得 AMI
echo "5. 測試取得最新的 Amazon Linux 2 AMI..."
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" "Name=state,Values=available" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --region "$REGION" \
    --output text 2>/dev/null || echo "")
if [ -n "$AMI_ID" ] && [ "$AMI_ID" != "None" ]; then
    echo "✅ 取得 AMI: $AMI_ID"
else
    echo "❌ 無法取得 AMI"
fi
echo ""

echo "=== 診斷完成 ==="
