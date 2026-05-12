#!/bin/bash
# 網站切換部署腳本
# 用途：快速切換並部署不同網站到 AWS EC2 服務器

# ===============================================================================
# 配置區
# ===============================================================================

# AWS EC2 服務器配置
AWS_SERVER_1="35.74.79.10"      # AWS 主服務器 1
AWS_SERVER_2="35.78.244.92"     # AWS 主服務器 2
WEB_ROOT="/var/www/html"        # 網站根目錄

# SSH 配置（自動檢測）
# 腳本會自動嘗試以下方式：
# 1. 檢測 ~/.ssh/ 目錄中的 .pem 文件
# 2. 自動檢測 EC2 用戶名（ec2-user, ubuntu, admin）
EC2_KEY=""                      # 留空則自動檢測
EC2_USER=""                     # 留空則自動檢測

# 網站目錄配置
WEBSITES_DIR="/Users/ckchiu/Desktop/Project/websites"
SITE1_DIR="$WEBSITES_DIR/site1-test"      # 測試網站
SITE2_DIR="$WEBSITES_DIR/site2-gaming"    # 博弈網站

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ===============================================================================
# 函數定義
# ===============================================================================

# 自動檢測 SSH 密鑰
detect_ssh_key() {
    if [ -n "$EC2_KEY" ] && [ -f "$EC2_KEY" ]; then
        return 0
    fi
    
    echo -e "${YELLOW}🔍 自動檢測 SSH 密鑰...${NC}"
    
    # 搜尋 ~/.ssh/ 目錄中的 .pem 文件
    local keys=(~/.ssh/*.pem)
    
    if [ -f "${keys[0]}" ]; then
        if [ ${#keys[@]} -eq 1 ]; then
            EC2_KEY="${keys[0]}"
            echo -e "${GREEN}✓ 找到密鑰：$EC2_KEY${NC}"
            return 0
        else
            echo -e "${CYAN}找到多個密鑰文件：${NC}"
            local i=1
            for key in "${keys[@]}"; do
                echo "  $i) $(basename $key)"
                ((i++))
            done
            echo ""
            read -p "請選擇密鑰編號 [1-${#keys[@]}]: " choice
            if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#keys[@]} ]; then
                EC2_KEY="${keys[$((choice-1))]}"
                echo -e "${GREEN}✓ 使用密鑰：$EC2_KEY${NC}"
                return 0
            else
                echo -e "${RED}✗ 無效的選擇${NC}"
                return 1
            fi
        fi
    fi
    
    echo -e "${RED}✗ 找不到 SSH 密鑰${NC}"
    echo "請將 .pem 文件放在 ~/.ssh/ 目錄中"
    return 1
}

# 檢查並修正密鑰權限
check_key_permission() {
    local key=$1
    local perm=$(stat -f "%A" "$key" 2>/dev/null || stat -c "%a" "$key" 2>/dev/null)
    
    if [ "$perm" != "400" ] && [ "$perm" != "600" ]; then
        echo -e "${YELLOW}修正密鑰權限...${NC}"
        chmod 400 "$key"
        echo -e "${GREEN}✓ 權限已設定為 400${NC}"
    fi
}

# 自動檢測 EC2 用戶名
detect_ec2_user() {
    local server=$1
    
    if [ -n "$EC2_USER" ]; then
        return 0
    fi
    
    echo -e "${YELLOW}檢測 EC2 用戶名...${NC}"
    
    # 嘗試常見的用戶名
    for user in ec2-user ubuntu admin root; do
        if ssh -i "$EC2_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o BatchMode=yes "$user@$server" "echo 'ok'" &>/dev/null; then
            EC2_USER="$user"
            echo -e "${GREEN}✓ 用戶名：$EC2_USER${NC}"
            return 0
        fi
    done
    
    echo -e "${RED}✗ 無法自動檢測用戶名${NC}"
    return 1
}

# 顯示使用說明
show_usage() {
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           網站切換部署工具 v1.0                           ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}使用方式：${NC}"
    echo -e "  $0 [網站編號]"
    echo ""
    echo -e "${YELLOW}可用的網站：${NC}"
    echo -e "  ${GREEN}1${NC} - DNS 測試網站（藍色 AWS + 紅色 Google）"
    echo -e "  ${GREEN}2${NC} - 博弈網站（皇冠娛樂城）"
    echo ""
    echo -e "${YELLOW}範例：${NC}"
    echo -e "  $0 1    # 部署測試網站"
    echo -e "  $0 2    # 部署博弈網站"
    echo ""
}

# 檢查 SSH 連線
check_ssh_connection() {
    local server=$1
    echo -e "${CYAN}檢查與 $server 的連線...${NC}"
    
    # 確保已檢測到用戶名
    if [ -z "$EC2_USER" ]; then
        detect_ec2_user "$server" || return 1
    fi
    
    if ssh -i "$EC2_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o BatchMode=yes "$EC2_USER@$server" "echo 'Connection OK'" &>/dev/null; then
        echo -e "${GREEN}✓ 連線成功 ($EC2_USER@$server)${NC}"
        return 0
    else
        echo -e "${RED}✗ 連線失敗${NC}"
        return 1
    fi
}

# 部署網站到單台服務器
deploy_to_server() {
    local server=$1
    local source_file=$2
    local target_name=$3
    
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}部署到服務器: $server${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # 檢查連線
    if ! check_ssh_connection "$server"; then
        echo -e "${RED}✗ 無法連線到 $server，跳過此服務器${NC}"
        return 1
    fi
    
    # 備份現有網站
    echo -e "${YELLOW}備份現有網站...${NC}"
    ssh -i "$EC2_KEY" "$EC2_USER@$server" "sudo cp $WEB_ROOT/index.html $WEB_ROOT/index.html.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true"
    
    # 上傳新網站
    echo -e "${YELLOW}上傳新網站文件...${NC}"
    scp -i "$EC2_KEY" "$source_file" "$EC2_USER@$server:/tmp/index.html"
    
    # 移動到網站目錄並設置權限
    echo -e "${YELLOW}設置文件權限...${NC}"
    ssh -i "$EC2_KEY" "$EC2_USER@$server" "sudo mv /tmp/index.html $WEB_ROOT/index.html && sudo chmod 644 $WEB_ROOT/index.html"
    
    # 重啟 Web 服務器（如果需要）
    echo -e "${YELLOW}重啟 Web 服務...${NC}"
    ssh -i "$EC2_KEY" "$EC2_USER@$server" "sudo systemctl restart httpd 2>/dev/null || sudo systemctl restart nginx 2>/dev/null || true"
    
    echo -e "${GREEN}✓ 部署完成${NC}"
    return 0
}

# 部署網站（兩台 AWS 服務器）
deploy_website() {
    local site_number=$1
    local site_dir=""
    local site_name=""
    
    case $site_number in
        1)
            site_dir="$SITE1_DIR"
            site_name="DNS 測試網站"
            ;;
        2)
            site_dir="$SITE2_DIR"
            site_name="博弈網站"
            ;;
        *)
            echo -e "${RED}錯誤：無效的網站編號${NC}"
            show_usage
            exit 1
            ;;
    esac
    
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  開始部署：$site_name${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # 檢查網站文件是否存在
    if [ ! -f "$site_dir/aws.html" ] || [ ! -f "$site_dir/google.html" ]; then
        echo -e "${RED}錯誤：找不到網站文件${NC}"
        echo -e "請確認以下文件存在："
        echo -e "  - $site_dir/aws.html"
        echo -e "  - $site_dir/google.html"
        exit 1
    fi
    
    # 自動檢測 SSH 密鑰
    if ! detect_ssh_key; then
        exit 1
    fi
    
    # 檢查密鑰權限
    check_key_permission "$EC2_KEY"
    
    # 顯示部署信息
    echo ""
    echo -e "${CYAN}網站目錄：${NC}$site_dir"
    echo -e "${CYAN}SSH 密鑰：${NC}$EC2_KEY"
    echo -e "${CYAN}目標服務器：${NC}"
    echo -e "  1. $AWS_SERVER_1 (AWS 主服務器 1)"
    echo -e "  2. $AWS_SERVER_2 (AWS 主服務器 2)"
    echo ""
    
    # 確認部署
    read -p "$(echo -e ${YELLOW}確定要部署嗎？[y/N]: ${NC})" confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}已取消部署${NC}"
        exit 0
    fi
    
    echo ""
    
    # 部署到兩台 AWS 服務器
    local success_count=0
    
    # 部署到服務器 1（使用 aws.html）
    if deploy_to_server "$AWS_SERVER_1" "$site_dir/aws.html" "AWS Server 1"; then
        ((success_count++))
    fi
    
    # 部署到服務器 2（使用 aws.html）
    if deploy_to_server "$AWS_SERVER_2" "$site_dir/aws.html" "AWS Server 2"; then
        ((success_count++))
    fi
    
    # 顯示部署結果
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  部署完成！${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}部署統計：${NC}"
    echo -e "  成功：${GREEN}$success_count${NC} / 2 台服務器"
    echo ""
    echo -e "${CYAN}訪問網址：${NC}"
    echo -e "  http://$AWS_SERVER_1"
    echo -e "  http://$AWS_SERVER_2"
    echo -e "  http://www.clouddeployment168.site (透過 DNS)"
    echo ""
    
    if [ $success_count -eq 2 ]; then
        echo -e "${GREEN}✓ 所有服務器部署成功！${NC}"
    elif [ $success_count -gt 0 ]; then
        echo -e "${YELLOW}⚠ 部分服務器部署成功${NC}"
    else
        echo -e "${RED}✗ 所有服務器部署失敗${NC}"
        exit 1
    fi
}

# 顯示當前部署狀態
show_status() {
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           當前部署狀態                                     ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # 自動檢測 SSH 密鑰
    if ! detect_ssh_key; then
        echo -e "${RED}無法檢查狀態：找不到 SSH 密鑰${NC}"
        return 1
    fi
    
    # 檢查密鑰權限
    check_key_permission "$EC2_KEY"
    
    for server in "$AWS_SERVER_1" "$AWS_SERVER_2"; do
        echo -e "${YELLOW}服務器: $server${NC}"
        if check_ssh_connection "$server"; then
            # 獲取網站標題
            local title=$(ssh -i "$EC2_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$server" "grep -oP '(?<=<title>).*(?=</title>)' $WEB_ROOT/index.html 2>/dev/null || echo '未知'")
            echo -e "  當前網站: ${GREEN}$title${NC}"
            
            # 測試 HTTP 訪問
            if curl -s --connect-timeout 3 "http://$server" > /dev/null; then
                echo -e "  HTTP 狀態: ${GREEN}✓ 可訪問${NC}"
            else
                echo -e "  HTTP 狀態: ${RED}✗ 無法訪問${NC}"
            fi
        fi
        echo ""
    done
}

# ===============================================================================
# 主程序
# ===============================================================================

# 檢查參數
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

# 處理命令
case $1 in
    1|2)
        deploy_website "$1"
        ;;
    status)
        show_status
        ;;
    -h|--help)
        show_usage
        ;;
    *)
        echo -e "${RED}錯誤：無效的參數${NC}"
        show_usage
        exit 1
        ;;
esac
