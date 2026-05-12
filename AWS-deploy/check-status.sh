#!/bin/bash

# AWS 運行狀況檢查腳本（完全禁用代理）

# 完全禁用所有代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY
unset socks_proxy SOCKS_PROXY socks5_proxy SOCKS5_PROXY
unset GIT_HTTP_PROXY GIT_HTTPS_PROXY

export http_proxy=""
export https_proxy=""
export HTTP_PROXY=""
export HTTPS_PROXY=""
export all_proxy=""
export ALL_PROXY=""

echo "🔍 AWS 運行狀況檢查"
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
    echo ""
    echo "   請在新的終端視窗執行此腳本："
    echo "   open -a Terminal"
    echo "   cd ~/Desktop/Project/AWS-deploy"
    echo "   ./check-status.sh"
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
    printf "   %-25s %-12s %-15s %-12s %s\n" "名稱" "狀態" "IP 地址" "類型" "實例 ID"
    echo "   ---------------------------------------------------------------------------------"
    
    echo "$INSTANCES" | while read INSTANCE_ID STATE PUBLIC_IP INSTANCE_TYPE NAME; do
        # 狀態圖標
        case $STATE in
            running)
                STATUS_ICON="🟢"
                ;;
            stopped)
                STATUS_ICON="🔴"
                ;;
            pending)
                STATUS_ICON="🟡"
                ;;
            *)
                STATUS_ICON="⚪"
                ;;
        esac
        
        printf "   %-25s %s %-10s %-15s %-12s %s\n" "$NAME" "$STATUS_ICON" "$STATE" "${PUBLIC_IP:-N/A}" "$INSTANCE_TYPE" "$INSTANCE_ID"
    done
fi

echo ""

# 3. 檢查運行中的實例詳情
echo "3️⃣  運行中實例詳情..."
RUNNING_INSTANCES=$(aws ec2 describe-instances \
    --region ap-northeast-1 \
    --filters "Name=instance-state-name,Values=running" \
    --query 'Reservations[].Instances[].[InstanceId,PublicIpAddress,Tags[?Key==`Name`].Value|[0],KeyName]' \
    --output text 2>/dev/null)

if [ -z "$RUNNING_INSTANCES" ]; then
    echo "   ℹ️  沒有運行中的實例"
else
    echo ""
    echo "$RUNNING_INSTANCES" | while read INSTANCE_ID PUBLIC_IP NAME KEY_NAME; do
        echo "   📦 $NAME"
        echo "      實例 ID: $INSTANCE_ID"
        echo "      公網 IP: $PUBLIC_IP"
        echo "      SSH Key: $KEY_NAME"
        
        # 根據名稱顯示訪問方式
        case $NAME in
            *Pokemon*)
                echo "      🎮 遊戲網址: http://$PUBLIC_IP"
                ;;
            *Globalping*)
                echo "      🔍 SSH 連線: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP"
                echo "      📝 執行檢測: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP '/opt/globalping-checker/run_check.sh'"
                ;;
            *DNS*)
                echo "      🌐 API 端點: http://$PUBLIC_IP:8000/docs"
                ;;
        esac
        
        echo ""
    done
fi

# 4. 檢查安全組
echo "4️⃣  檢查安全組..."
SECURITY_GROUPS=$(aws ec2 describe-security-groups \
    --region ap-northeast-1 \
    --filters "Name=group-name,Values=*-sg" \
    --query 'SecurityGroups[].[GroupName,GroupId]' \
    --output text 2>/dev/null)

if [ -z "$SECURITY_GROUPS" ]; then
    echo "   ℹ️  沒有相關安全組"
else
    echo ""
    echo "$SECURITY_GROUPS" | while read NAME GROUP_ID; do
        echo "   🔒 $NAME ($GROUP_ID)"
    done
fi

echo ""

# 5. 成本估算
echo "5️⃣  成本估算..."
RUNNING_COUNT=$(echo "$RUNNING_INSTANCES" | grep -c "i-" 2>/dev/null || echo "0")
STOPPED_COUNT=$(aws ec2 describe-instances \
    --region ap-northeast-1 \
    --filters "Name=instance-state-name,Values=stopped" \
    --query 'Reservations[].Instances[].InstanceId' \
    --output text 2>/dev/null | wc -w | tr -d ' ')

echo ""
echo "   運行中實例: $RUNNING_COUNT"
echo "   停止的實例: $STOPPED_COUNT"

if [ "$RUNNING_COUNT" -gt 0 ]; then
    # 簡單估算（假設都是 t3.micro）
    ESTIMATED_COST=$(echo "$RUNNING_COUNT * 7.5" | bc)
    echo "   預估月成本: ~\$${ESTIMATED_COST} USD"
    echo "   （假設 t3.micro 24/7 運行）"
fi

echo ""
echo "========================================"
echo "✅ 檢查完成"
echo "========================================"
echo ""

# 6. 快速操作提示
if [ "$RUNNING_COUNT" -gt 0 ]; then
    echo "💡 快速操作："
    echo "   查看詳細狀態: ./aws-manager.sh (選項 7)"
    echo "   停止所有實例: ./aws-manager.sh (選項 11)"
    echo "   更新代碼: ./aws-manager.sh (選項 10)"
    echo ""
fi
