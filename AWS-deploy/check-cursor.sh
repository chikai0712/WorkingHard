#!/bin/bash

# 在 Cursor 中檢查 AWS 狀態（自動處理代理）

# 禁用所有代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY
unset socks_proxy SOCKS_PROXY socks5_proxy SOCKS5_PROXY
unset GIT_HTTP_PROXY GIT_HTTPS_PROXY

export NO_PROXY="*"

echo "🔍 AWS 運行狀況檢查（Cursor 版本）"
echo "========================================"
echo ""

# 1. 檢查 AWS 連線
echo "1️⃣  檢查 AWS 連線..."
if aws sts get-caller-identity --no-cli-pager 2>/dev/null; then
    echo "   ✅ AWS CLI 連線正常"
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
    echo "   帳號: $ACCOUNT_ID"
else
    echo "   ❌ AWS CLI 連線失敗"
    exit 1
fi

echo ""

# 2. 檢查所有 EC2 實例
echo "2️⃣  檢查 EC2 實例..."
INSTANCES=$(aws ec2 describe-instances \
    --region ap-northeast-1 \
    --query 'Reservations[].Instances[].[InstanceId,State.Name,PublicIpAddress,InstanceType,Tags[?Key==`Name`].Value|[0]]' \
    --output text 2>/dev/null)

if [ -z "$INSTANCES" ]; then
    echo "   ℹ️  沒有 EC2 實例"
else
    echo ""
    printf "   %-30s %-12s %-16s %-12s\n" "名稱" "狀態" "IP 地址" "類型"
    echo "   --------------------------------------------------------------------------------"
    
    echo "$INSTANCES" | while read INSTANCE_ID STATE PUBLIC_IP INSTANCE_TYPE NAME; do
        case $STATE in
            running)
                STATUS="🟢 $STATE"
                ;;
            stopped)
                STATUS="🔴 $STATE"
                ;;
            *)
                STATUS="⚪ $STATE"
                ;;
        esac
        
        printf "   %-30s %-12s %-16s %-12s\n" "$NAME" "$STATUS" "${PUBLIC_IP:-N/A}" "$INSTANCE_TYPE"
    done
fi

echo ""

# 3. 檢查運行中的實例
echo "3️⃣  運行中實例詳情..."
RUNNING=$(aws ec2 describe-instances \
    --region ap-northeast-1 \
    --filters "Name=instance-state-name,Values=running" \
    --query 'Reservations[].Instances[].[InstanceId,PublicIpAddress,Tags[?Key==`Name`].Value|[0],KeyName]' \
    --output text 2>/dev/null)

if [ -z "$RUNNING" ]; then
    echo "   ℹ️  沒有運行中的實例"
else
    echo ""
    echo "$RUNNING" | while read ID IP NAME KEY; do
        echo "   📦 $NAME"
        echo "      實例: $ID"
        echo "      IP: $IP"
        echo "      Key: $KEY"
        
        case $NAME in
            *Pokemon*)
                echo "      🎮 訪問: http://$IP"
                ;;
            *Globalping*)
                echo "      🔍 SSH: ssh -i ~/.ssh/$KEY.pem ec2-user@$IP"
                ;;
            *DNS*)
                echo "      🌐 API: http://$IP:8000/docs"
                ;;
        esac
        echo ""
    done
fi

echo "========================================"
echo "✅ 檢查完成"
echo "========================================"
