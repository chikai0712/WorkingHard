#!/bin/bash

# 修復 SSH 連線問題的腳本

echo "🔧 修復 SSH 連線問題..."
echo ""

# 檢查密鑰文件
echo "1. 檢查 SSH 密鑰..."
for KEY in pokemon-game-key globalping-checker-key dns-monitoring-key; do
    if [ -f ~/.ssh/$KEY.pem ]; then
        echo "  ✓ 找到: $KEY.pem"
        chmod 400 ~/.ssh/$KEY.pem
        echo "    權限已設置為 400"
    else
        echo "  ✗ 未找到: $KEY.pem"
    fi
done

echo ""
echo "2. 檢查運行中的實例..."

# 獲取所有運行中的實例
INSTANCES=$(aws ec2 describe-instances \
    --region ap-northeast-1 \
    --filters "Name=instance-state-name,Values=running" \
    --query 'Reservations[].Instances[].[InstanceId,PublicIpAddress,Tags[?Key==`Name`].Value|[0],KeyName]' \
    --output text)

if [ -z "$INSTANCES" ]; then
    echo "  ℹ️  沒有運行中的實例"
else
    echo "$INSTANCES" | while read INSTANCE_ID PUBLIC_IP NAME KEY_NAME; do
        echo ""
        echo "  實例: $NAME"
        echo "    ID: $INSTANCE_ID"
        echo "    IP: $PUBLIC_IP"
        echo "    Key: $KEY_NAME"
        
        # 測試 SSH 連線
        if [ -f ~/.ssh/$KEY_NAME.pem ]; then
            echo "    測試 SSH 連線..."
            if ssh -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no -o ConnectTimeout=5 ec2-user@$PUBLIC_IP "echo '連線成功'" 2>/dev/null; then
                echo "    ✅ SSH 連線正常"
            else
                echo "    ❌ SSH 連線失敗"
                echo ""
                echo "    建議操作："
                echo "      1. 等待實例完全啟動（可能需要 1-2 分鐘）"
                echo "      2. 檢查安全組是否允許你的 IP"
                echo "      3. 手動測試: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP"
            fi
        else
            echo "    ⚠️  密鑰文件不存在: ~/.ssh/$KEY_NAME.pem"
        fi
    done
fi

echo ""
echo "3. 檢查安全組規則..."

# 獲取所有安全組
SECURITY_GROUPS=$(aws ec2 describe-security-groups \
    --region ap-northeast-1 \
    --filters "Name=group-name,Values=*-sg" \
    --query 'SecurityGroups[].[GroupId,GroupName]' \
    --output text)

if [ -n "$SECURITY_GROUPS" ]; then
    echo "$SECURITY_GROUPS" | while read GROUP_ID GROUP_NAME; do
        echo ""
        echo "  安全組: $GROUP_NAME ($GROUP_ID)"
        
        # 檢查 SSH 規則
        SSH_RULE=$(aws ec2 describe-security-groups \
            --region ap-northeast-1 \
            --group-ids $GROUP_ID \
            --query 'SecurityGroups[0].IpPermissions[?FromPort==`22`]' \
            --output text)
        
        if [ -n "$SSH_RULE" ]; then
            echo "    ✅ 允許 SSH (port 22)"
        else
            echo "    ❌ 未允許 SSH"
        fi
    done
fi

echo ""
echo "✅ 檢查完成"
echo ""
echo "💡 如果 SSH 仍然無法連線，請嘗試："
echo "  1. 等待 2-3 分鐘讓實例完全啟動"
echo "  2. 檢查你的本地網路是否允許 SSH 連線"
echo "  3. 在 AWS Console 檢查實例狀態檢查是否通過"
echo ""
