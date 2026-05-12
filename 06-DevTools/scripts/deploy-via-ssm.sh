#!/bin/bash

# 使用 AWS SSM 部署網站到 EC2
# 不需要 SSH，使用 AWS Systems Manager

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}🚀 使用 AWS SSM 部署博弈網站${NC}"
echo ""

# 檢查 AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ 錯誤：未安裝 AWS CLI${NC}"
    echo "請執行：brew install awscli"
    exit 1
fi

# EC2 實例 IP
AWS_SERVER_1="35.74.79.10"
AWS_SERVER_2="35.78.244.92"

# 網站文件路徑
WEBSITE_FILE="/Users/ckchiu/Desktop/Project/websites/site2-gaming/aws.html"

if [ ! -f "$WEBSITE_FILE" ]; then
    echo -e "${RED}❌ 錯誤：找不到網站文件${NC}"
    echo "路徑：$WEBSITE_FILE"
    exit 1
fi

echo -e "${CYAN}網站文件：${NC}$WEBSITE_FILE"
echo ""

# 取得實例 ID
echo -e "${YELLOW}🔍 查詢 EC2 實例 ID...${NC}"

INSTANCE_1=$(aws ec2 describe-instances \
    --filters "Name=ip-address,Values=$AWS_SERVER_1" "Name=instance-state-name,Values=running" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text 2>/dev/null)

INSTANCE_2=$(aws ec2 describe-instances \
    --filters "Name=ip-address,Values=$AWS_SERVER_2" "Name=instance-state-name,Values=running" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text 2>/dev/null)

if [ "$INSTANCE_1" == "None" ] || [ -z "$INSTANCE_1" ]; then
    echo -e "${RED}✗ 找不到實例：$AWS_SERVER_1${NC}"
    INSTANCE_1=""
else
    echo -e "${GREEN}✓ 實例 1：$INSTANCE_1 ($AWS_SERVER_1)${NC}"
fi

if [ "$INSTANCE_2" == "None" ] || [ -z "$INSTANCE_2" ]; then
    echo -e "${RED}✗ 找不到實例：$AWS_SERVER_2${NC}"
    INSTANCE_2=""
else
    echo -e "${GREEN}✓ 實例 2：$INSTANCE_2 ($AWS_SERVER_2)${NC}"
fi

if [ -z "$INSTANCE_1" ] && [ -z "$INSTANCE_2" ]; then
    echo -e "${RED}❌ 錯誤：找不到任何實例${NC}"
    exit 1
fi

echo ""
read -p "$(echo -e ${YELLOW}確定要部署嗎？[y/N]: ${NC})" confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}已取消部署${NC}"
    exit 0
fi

echo ""

# 讀取網站內容並轉義
WEBSITE_CONTENT=$(cat "$WEBSITE_FILE" | sed 's/"/\\"/g' | sed "s/'/\\'/g")

# 部署函數
deploy_to_instance() {
    local instance_id=$1
    local server_ip=$2
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}部署到：$server_ip ($instance_id)${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # 使用 SSM 執行命令
    echo -e "${YELLOW}上傳網站文件...${NC}"
    
    COMMAND_ID=$(aws ssm send-command \
        --instance-ids "$instance_id" \
        --document-name "AWS-RunShellScript" \
        --parameters "commands=[
            'sudo cp /var/www/html/index.html /var/www/html/index.html.backup.\$(date +%Y%m%d_%H%M%S) 2>/dev/null || true',
            'sudo tee /var/www/html/index.html > /dev/null << '\''EOFHTML'\''
$WEBSITE_CONTENT
EOFHTML',
            'sudo chmod 644 /var/www/html/index.html',
            'sudo systemctl restart httpd 2>/dev/null || sudo systemctl restart nginx 2>/dev/null || true',
            'echo \"部署完成\"'
        ]" \
        --output text \
        --query 'Command.CommandId' 2>&1)
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ 部署失敗${NC}"
        echo "$COMMAND_ID"
        return 1
    fi
    
    echo -e "${YELLOW}等待命令執行...${NC}"
    sleep 3
    
    # 檢查執行結果
    STATUS=$(aws ssm get-command-invocation \
        --command-id "$COMMAND_ID" \
        --instance-id "$instance_id" \
        --query 'Status' \
        --output text 2>/dev/null)
    
    if [ "$STATUS" == "Success" ]; then
        echo -e "${GREEN}✓ 部署成功${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ 狀態：$STATUS${NC}"
        return 1
    fi
}

# 部署到兩台服務器
success_count=0

if [ -n "$INSTANCE_1" ]; then
    if deploy_to_instance "$INSTANCE_1" "$AWS_SERVER_1"; then
        ((success_count++))
    fi
    echo ""
fi

if [ -n "$INSTANCE_2" ]; then
    if deploy_to_instance "$INSTANCE_2" "$AWS_SERVER_2"; then
        ((success_count++))
    fi
    echo ""
fi

# 顯示結果
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  部署完成！${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}部署統計：${NC}"
echo -e "  成功：${GREEN}$success_count${NC} 台服務器"
echo ""
echo -e "${CYAN}訪問網址：${NC}"
[ -n "$INSTANCE_1" ] && echo -e "  http://$AWS_SERVER_1"
[ -n "$INSTANCE_2" ] && echo -e "  http://$AWS_SERVER_2"
echo -e "  http://www.clouddeployment168.site (透過 DNS)"
echo ""

if [ $success_count -gt 0 ]; then
    echo -e "${GREEN}✓ 部署成功！${NC}"
else
    echo -e "${RED}✗ 部署失敗${NC}"
    exit 1
fi
