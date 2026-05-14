#!/bin/bash

# AWS 部署統一管理腳本
# 用途：管理所有 AWS 部署的項目

set -e

# 禁用代理（避免 AWS CLI 連線問題）
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================"
echo "AWS 部署管理系統"
echo "========================================${NC}"
echo ""

# 顯示菜單
show_menu() {
    echo -e "${GREEN}請選擇操作：${NC}"
    echo ""
    echo "部署新服務："
    echo "  1) 部署 Pokemon 遊戲"
    echo "  2) 部署 Globalping Checker"
    echo "  3) 部署 DNS 監控系統"
    echo ""
    echo "檢查狀態："
    echo "  4) 檢查 Pokemon 遊戲狀態"
    echo "  5) 檢查 Globalping Checker 狀態"
    echo "  6) 檢查 DNS 監控系統狀態"
    echo "  7) 檢查所有服務狀態"
    echo ""
    echo "更新服務："
    echo "  8) 更新 Pokemon 遊戲"
    echo "  9) 更新 Globalping 域名列表"
    echo ""
    echo "管理操作："
    echo "  10) 停止所有服務"
    echo "  11) 啟動所有服務"
    echo "  12) 查看成本估算"
    echo ""
    echo "  0) 退出"
    echo ""
}

# 檢查所有服務狀態
check_all_status() {
    echo -e "${BLUE}========================================"
    echo "檢查所有服務狀態"
    echo "========================================${NC}"
    echo ""
    
    # Pokemon 遊戲
    echo -e "${YELLOW}1. Pokemon 遊戲${NC}"
    bash "$(dirname "$0")/check-game-status.sh" 2>/dev/null || echo "  ❌ 未部署"
    echo ""
    
    # Globalping Checker
    echo -e "${YELLOW}2. Globalping Checker${NC}"
    bash "$(dirname "$0")/check-globalping-status.sh" 2>/dev/null || echo "  ❌ 未部署"
    echo ""
    
    # DNS 監控系統
    echo -e "${YELLOW}3. DNS 監控系統${NC}"
    bash "$(dirname "$0")/check-dns-monitoring-status.sh" 2>/dev/null || echo "  ❌ 未部署"
    echo ""
}

# 停止所有服務
stop_all_services() {
    echo -e "${YELLOW}停止所有 EC2 實例...${NC}"
    
    INSTANCES=$(aws ec2 describe-instances \
        --region ap-northeast-1 \
        --filters "Name=instance-state-name,Values=running" \
        --query 'Reservations[].Instances[].[InstanceId,Tags[?Key==`Name`].Value|[0]]' \
        --output text | grep -E "Pokemon-Game-Server|Globalping-Checker-Server|DNS-Monitoring-Server")
    
    if [ -z "$INSTANCES" ]; then
        echo "  ℹ️  沒有運行中的實例"
        return
    fi
    
    echo "$INSTANCES" | while read INSTANCE_ID NAME; do
        echo "  停止: $NAME ($INSTANCE_ID)"
        aws ec2 stop-instances --instance-ids $INSTANCE_ID --region ap-northeast-1 > /dev/null
    done
    
    echo -e "${GREEN}✅ 所有實例已停止${NC}"
}

# 啟動所有服務
start_all_services() {
    echo -e "${YELLOW}啟動所有 EC2 實例...${NC}"
    
    INSTANCES=$(aws ec2 describe-instances \
        --region ap-northeast-1 \
        --filters "Name=instance-state-name,Values=stopped" \
        --query 'Reservations[].Instances[].[InstanceId,Tags[?Key==`Name`].Value|[0]]' \
        --output text | grep -E "Pokemon-Game-Server|Globalping-Checker-Server|DNS-Monitoring-Server")
    
    if [ -z "$INSTANCES" ]; then
        echo "  ℹ️  沒有停止的實例"
        return
    fi
    
    echo "$INSTANCES" | while read INSTANCE_ID NAME; do
        echo "  啟動: $NAME ($INSTANCE_ID)"
        aws ec2 start-instances --instance-ids $INSTANCE_ID --region ap-northeast-1 > /dev/null
    done
    
    echo -e "${GREEN}✅ 所有實例已啟動${NC}"
}

# 成本估算
show_cost_estimate() {
    echo -e "${BLUE}========================================"
    echo "AWS 成本估算 (ap-northeast-1)"
    echo "========================================${NC}"
    echo ""
    
    # 統計運行中的實例
    RUNNING_INSTANCES=$(aws ec2 describe-instances \
        --region ap-northeast-1 \
        --filters "Name=instance-state-name,Values=running" \
        --query 'Reservations[].Instances[].[InstanceType,Tags[?Key==`Name`].Value|[0]]' \
        --output text | grep -E "Pokemon-Game-Server|Globalping-Checker-Server|DNS-Monitoring-Server")
    
    if [ -z "$RUNNING_INSTANCES" ]; then
        echo "  ℹ️  沒有運行中的實例"
        return
    fi
    
    echo "運行中的實例："
    echo ""
    
    TOTAL_COST=0
    
    echo "$RUNNING_INSTANCES" | while read INSTANCE_TYPE NAME; do
        case $INSTANCE_TYPE in
            t3.micro)
                COST=7.50
                ;;
            t3.small)
                COST=15.00
                ;;
            t3.medium)
                COST=30.00
                ;;
            *)
                COST=0
                ;;
        esac
        
        echo "  $NAME"
        echo "    類型: $INSTANCE_TYPE"
        echo "    月成本: ~\$${COST} USD"
        echo ""
        
        TOTAL_COST=$(echo "$TOTAL_COST + $COST" | bc)
    done
    
    echo "預估總成本: ~\$${TOTAL_COST} USD/月"
    echo ""
    echo "💡 提示："
    echo "  - 使用 AWS 免費方案可享 12 個月免費 (750 小時/月 t2.micro/t3.micro)"
    echo "  - 停止不使用的實例可節省成本"
    echo "  - 使用 Spot 實例可節省最多 90% 成本"
    echo ""
}

# 主循環
while true; do
    show_menu
    read -p "請選擇 (0-13): " CHOICE
    echo ""
    
    case $CHOICE in
        1)
            bash "$(dirname "$0")/deploy-pokemon-game.sh"
            ;;
        2)
            bash "$(dirname "$0")/deploy-globalping-checker.sh"
            ;;
        3)
            bash "$(dirname "$0")/deploy-dns-monitoring.sh"
            ;;
        4)
            bash "$(dirname "$0")/check-game-status.sh"
            ;;
        5)
            bash "$(dirname "$0")/check-globalping-status.sh"
            ;;
        6)
            bash "$(dirname "$0")/check-dns-monitoring-status.sh"
            ;;
        7)
            check_all_status
            ;;
        8)
            bash "$(dirname "$0")/update-pokemon-game.sh"
            ;;
        9)
            bash "$(dirname "$0")/update-globalping-domains.sh"
            ;;
        10)
            bash "$(dirname "$0")/update-globalping-code.sh"
            ;;
        11)
            stop_all_services
            ;;
        12)
            start_all_services
            ;;
        13)
            show_cost_estimate
            ;;
        0)
            echo "退出"
            exit 0
            ;;
        *)
            echo -e "${RED}無效選擇${NC}"
            ;;
    esac
    
    echo ""
    read -p "按 Enter 繼續..."
    clear
done
