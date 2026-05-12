#!/bin/bash
# -------------------------------------------------------------------------------
# AWS EC2 網站自動部署腳本
# 功能：自動部署兩台 EC2，分別顯示 "我是 AWS" 和 "我是 Google"
# 
# 用法：
#   bash ./deploy-ec2-websites.sh
# 
# 前置需求：
#   1. 已安裝並配置 AWS CLI (aws configure)
#   2. 已有 Key Pair（或腳本會協助建立）
#   3. 已有 Security Group（或腳本會協助建立）
# -------------------------------------------------------------------------------

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置區域
REGION="${AWS_REGION:-ap-northeast-1}"
INSTANCE_TYPE="${INSTANCE_TYPE:-t3.micro}"  # 預設使用 t3.micro（Free Tier 適用）
KEY_NAME="${KEY_NAME:-dns-test-key}"
SECURITY_GROUP_NAME="${SECURITY_GROUP_NAME:-dns-test-sg}"
AMI_ID="${AMI_ID:-}"  # 留空則自動選擇最新的 Ubuntu 22.04 LTS
OS_TYPE="${OS_TYPE:-ubuntu}"  # 作業系統類型：ubuntu 或 amazon-linux

# 檢查 AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ 錯誤：未安裝 AWS CLI${NC}"
    echo "請執行：brew install awscli 或 pip3 install awscli"
    exit 1
fi

# 檢查 AWS 憑證
if ! aws sts get-caller-identity &>/dev/null; then
    echo -e "${RED}❌ 錯誤：AWS 憑證未配置${NC}"
    echo "請執行：aws configure"
    exit 1
fi

echo -e "${GREEN}=== AWS EC2 網站自動部署 ===${NC}\n"
echo -e "區域: ${CYAN}$REGION${NC}"
echo -e "實例類型: ${CYAN}$INSTANCE_TYPE${NC}"
echo ""

# -------------------------------------------------------------------------------
# 取得最新的 Ubuntu 22.04 LTS AMI ID
# -------------------------------------------------------------------------------
get_latest_ubuntu_ami() {
    local region=$1
    aws ec2 describe-images \
        --owners 099720109477 \
        --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" "Name=state,Values=available" \
        --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
        --region "$region" \
        --output text
}

# -------------------------------------------------------------------------------
# 取得最新的 Amazon Linux 2 AMI ID
# -------------------------------------------------------------------------------
get_latest_amazon_linux_ami() {
    local region=$1
    aws ec2 describe-images \
        --owners amazon \
        --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" "Name=state,Values=available" \
        --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
        --region "$region" \
        --output text
}

# -------------------------------------------------------------------------------
# 建立或取得 Key Pair
# -------------------------------------------------------------------------------
setup_key_pair() {
    local key_name=$1
    local key_file="$HOME/.ssh/${key_name}.pem"
    
    echo -e "${CYAN}📋 檢查 Key Pair: $key_name${NC}" >&2
    
    # 檢查 Key Pair 是否存在
    if aws ec2 describe-key-pairs --key-names "$key_name" --region "$REGION" &>/dev/null; then
        echo -e "${GREEN}✅ Key Pair 已存在${NC}" >&2
        
        # 檢查本地是否有私鑰
        if [ ! -f "$key_file" ]; then
            echo -e "${YELLOW}⚠️  本地沒有私鑰檔案: $key_file${NC}" >&2
            echo -e "${YELLOW}Key Pair 已存在於 AWS，但本地沒有私鑰檔案${NC}" >&2
            echo "" >&2
            echo -e "${CYAN}解決方案：${NC}" >&2
            echo "  選項 1: 刪除現有 Key Pair 並重新建立（推薦）" >&2
            echo -e "    ${YELLOW}aws ec2 delete-key-pair --key-name $key_name --region $REGION${NC}" >&2
            echo "    然後重新執行此腳本" >&2
            echo "" >&2
            echo "  選項 2: 使用不同的 Key Pair 名稱" >&2
            echo -e "    ${YELLOW}export KEY_NAME=my-key-$(date +%s)${NC}" >&2
            echo "    然後重新執行此腳本" >&2
            echo "" >&2
            echo "  選項 3: 如果您有私鑰檔案但路徑不同，請複製到: $key_file" >&2
            echo "" >&2
            read -p "是否要刪除現有 Key Pair 並重新建立？(y/N): " confirm <&1
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                echo -e "${YELLOW}正在刪除現有 Key Pair...${NC}" >&2
                aws ec2 delete-key-pair --key-name "$key_name" --region "$REGION" 2>/dev/null || true
                echo -e "${GREEN}✅ Key Pair 已刪除，將重新建立${NC}" >&2
                # 遞迴呼叫自己來重新建立
                setup_key_pair "$key_name"
                return $?
            else
                echo -e "${RED}❌ 無法繼續：需要私鑰檔案才能連線到 EC2${NC}" >&2
                return 1
            fi
        else
            echo -e "${GREEN}✅ 本地私鑰檔案存在: $key_file${NC}" >&2
            chmod 400 "$key_file" 2>/dev/null || true
        fi
    else
        echo -e "${YELLOW}建立新的 Key Pair: $key_name${NC}" >&2
        if ! aws ec2 create-key-pair \
            --key-name "$key_name" \
            --query 'KeyMaterial' \
            --output text \
            --region "$REGION" > "$key_file" 2>/dev/null; then
            echo -e "${RED}❌ 建立 Key Pair 失敗${NC}" >&2
            return 1
        fi
        
        chmod 400 "$key_file"
        echo -e "${GREEN}✅ Key Pair 已建立，私鑰已儲存到: $key_file${NC}" >&2
    fi
    
    echo "$key_file"
    return 0
}

# -------------------------------------------------------------------------------
# 建立或取得 Security Group
# -------------------------------------------------------------------------------
setup_security_group() {
    local sg_name=$1
    
    echo -e "${CYAN}📋 檢查 Security Group: $sg_name${NC}" >&2
    
    # 檢查 Security Group 是否存在
    local sg_id
    sg_id=$(aws ec2 describe-security-groups \
        --group-names "$sg_name" \
        --region "$REGION" \
        --query 'SecurityGroups[0].GroupId' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$sg_id" ] && [ "$sg_id" != "None" ]; then
        echo -e "${GREEN}✅ Security Group 已存在: $sg_id${NC}" >&2
    else
        echo -e "${YELLOW}建立新的 Security Group: $sg_name${NC}" >&2
        
        # 取得 VPC ID
        local vpc_id
        vpc_id=$(aws ec2 describe-vpcs \
            --filters "Name=isDefault,Values=true" \
            --region "$REGION" \
            --query 'Vpcs[0].VpcId' \
            --output text)
        
        if [ -z "$vpc_id" ] || [ "$vpc_id" = "None" ]; then
            echo -e "${RED}❌ 找不到預設 VPC${NC}" >&2
            return 1
        fi
        
        # 建立 Security Group
        sg_id=$(aws ec2 create-security-group \
            --group-name "$sg_name" \
            --description "DNS Test Security Group" \
            --vpc-id "$vpc_id" \
            --region "$REGION" \
            --query 'GroupId' \
            --output text 2>/dev/null)
        
        if [ -z "$sg_id" ] || [ "$sg_id" = "None" ]; then
            echo -e "${RED}❌ 建立 Security Group 失敗${NC}" >&2
            return 1
        fi
        
        # 取得本機 IP（設定超時避免卡住）
        local my_ip
        echo -e "${YELLOW}取得本機 IP...${NC}" >&2
        my_ip=$(curl -s --max-time 5 https://checkip.amazonaws.com/ 2>/dev/null || echo "0.0.0.0/0")
        if [ "$my_ip" = "0.0.0.0/0" ]; then
            echo -e "${YELLOW}⚠️  無法取得本機 IP，將開放所有 IP 的 SSH 存取（測試用）${NC}" >&2
        else
            echo -e "${GREEN}✅ 本機 IP: $my_ip${NC}" >&2
        fi
        
        # 開放 SSH (22)
        echo -e "${YELLOW}設定 Security Group 規則...${NC}" >&2
        if [ "$my_ip" != "0.0.0.0/0" ]; then
            aws ec2 authorize-security-group-ingress \
                --group-id "$sg_id" \
                --protocol tcp \
                --port 22 \
                --cidr "${my_ip}/32" \
                --region "$REGION" 2>/dev/null || true
        else
            # 如果無法取得 IP，開放所有 IP（僅測試用）
            aws ec2 authorize-security-group-ingress \
                --group-id "$sg_id" \
                --protocol tcp \
                --port 22 \
                --cidr "0.0.0.0/0" \
                --region "$REGION" 2>/dev/null || true
        fi
        
        # 開放 HTTP (80)
        aws ec2 authorize-security-group-ingress \
            --group-id "$sg_id" \
            --protocol tcp \
            --port 80 \
            --cidr "0.0.0.0/0" \
            --region "$REGION" &>/dev/null || true
        
        # 開放 HTTPS (443)
        aws ec2 authorize-security-group-ingress \
            --group-id "$sg_id" \
            --protocol tcp \
            --port 443 \
            --cidr "0.0.0.0/0" \
            --region "$REGION" &>/dev/null || true
        
        echo -e "${GREEN}✅ Security Group 已建立: $sg_id${NC}" >&2
    fi
    
    echo "$sg_id"
    return 0
}

# -------------------------------------------------------------------------------
# 建立網站內容（用於 User Data）
# -------------------------------------------------------------------------------
create_website_content() {
    local server_name=$1
    local ip_address=$2
    local bg_color=$3
    local os_type="${OS_TYPE:-ubuntu}"
    
    if [ "$os_type" = "ubuntu" ]; then
        # Ubuntu/Debian 系統
        cat <<EOF
#!/bin/bash
# 自動部署腳本（User Data）- Ubuntu

# 更新系統
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y

# 安裝 Nginx
apt-get install -y nginx

# 建立網站內容
cat > /var/www/html/index.html <<'HTML_EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>DNS Failover Test - $server_name</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background: $bg_color;
            color: white;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            margin: 0;
        }
        h1 { 
            font-size: 4em; 
            margin: 20px 0; 
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .ip { 
            font-size: 3em; 
            font-weight: bold; 
            margin: 20px 0;
            padding: 20px;
            background: rgba(255,255,255,0.2);
            border-radius: 10px;
        }
        .info {
            margin-top: 30px;
            font-size: 1.2em;
        }
    </style>
</head>
<body>
    <h1>我是 $server_name</h1>
    <div class="ip">$ip_address</div>
    <div class="info">
        <p>這是 $server_name EC2 實例</p>
        <p>時間: <span id="time"></span></p>
        <p>實例 ID: <span id="instance-id"></span></p>
    </div>
    <script>
        document.getElementById('time').textContent = new Date().toLocaleString();
        fetch('http://169.254.169.254/latest/meta-data/instance-id')
            .then(r => r.text())
            .then(id => document.getElementById('instance-id').textContent = id);
    </script>
</body>
</html>
HTML_EOF

# 啟動 Nginx
systemctl start nginx
systemctl enable nginx

# 確保防火牆允許 HTTP/HTTPS（Ubuntu 使用 ufw）
if command -v ufw &>/dev/null; then
    ufw allow 'Nginx Full' 2>/dev/null || ufw allow 80/tcp
    ufw allow 443/tcp
fi
EOF
    else
        # Amazon Linux 2 系統
        cat <<EOF
#!/bin/bash
# 自動部署腳本（User Data）- Amazon Linux 2

# 更新系統
yum update -y

# 安裝 Nginx
yum install -y nginx

# 建立網站內容
cat > /usr/share/nginx/html/index.html <<'HTML_EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>DNS Failover Test - $server_name</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background: $bg_color;
            color: white;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            margin: 0;
        }
        h1 { 
            font-size: 4em; 
            margin: 20px 0; 
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .ip { 
            font-size: 3em; 
            font-weight: bold; 
            margin: 20px 0;
            padding: 20px;
            background: rgba(255,255,255,0.2);
            border-radius: 10px;
        }
        .info {
            margin-top: 30px;
            font-size: 1.2em;
        }
    </style>
</head>
<body>
    <h1>我是 $server_name</h1>
    <div class="ip">$ip_address</div>
    <div class="info">
        <p>這是 $server_name EC2 實例</p>
        <p>時間: <span id="time"></span></p>
        <p>實例 ID: <span id="instance-id"></span></p>
    </div>
    <script>
        document.getElementById('time').textContent = new Date().toLocaleString();
        fetch('http://169.254.169.254/latest/meta-data/instance-id')
            .then(r => r.text())
            .then(id => document.getElementById('instance-id').textContent = id);
    </script>
</body>
</html>
HTML_EOF

# 啟動 Nginx
systemctl start nginx
systemctl enable nginx

# 確保防火牆允許 HTTP/HTTPS（如果使用 firewalld）
if command -v firewall-cmd &>/dev/null; then
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload
fi
EOF
    fi
}

# -------------------------------------------------------------------------------
# 啟動 EC2 實例
# -------------------------------------------------------------------------------
launch_instance() {
    local instance_name=$1
    local server_name=$2
    local ip_address=$3
    local bg_color=$4
    local ami_id=$5
    local key_name=$6
    local sg_id=$7
    
    echo -e "${CYAN}🚀 啟動 EC2 實例: $instance_name${NC}" >&2
    
    # 建立 User Data 臨時檔案（使用 file:// 前綴讓 AWS CLI 自動處理編碼）
    local user_data_file
    user_data_file=$(mktemp)
    create_website_content "$server_name" "$ip_address" "$bg_color" "$OS_TYPE" > "$user_data_file"
    
    # 驗證檔案編碼（確保是 UTF-8，沒有 BOM）
    if ! file "$user_data_file" | grep -q "UTF-8\|ASCII\|text"; then
        echo -e "${YELLOW}⚠️  警告: User Data 檔案可能不是純文字格式${NC}" >&2
    fi
    
    echo -e "${YELLOW}正在啟動實例...${NC}" >&2
    
    # 啟動實例（使用 file:// 前綴）
    local instance_id
    local aws_output
    aws_output=$(aws ec2 run-instances \
        --image-id "$ami_id" \
        --instance-type "$INSTANCE_TYPE" \
        --key-name "$key_name" \
        --security-group-ids "$sg_id" \
        --user-data "file://$user_data_file" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$instance_name}]" \
        --region "$REGION" \
        --query 'Instances[0].InstanceId' \
        --output text 2>&1)
    
    instance_id="$aws_output"
    
    # 清理臨時檔案
    rm -f "$user_data_file"
    
    # 檢查是否有錯誤
    if [ -z "$instance_id" ] || [[ "$instance_id" =~ "error occurred" ]] || [[ "$instance_id" =~ "Error" ]] || [[ "$instance_id" =~ "An error" ]]; then
        echo -e "${RED}❌ 啟動實例失敗${NC}" >&2
        echo -e "${RED}錯誤訊息: $instance_id${NC}" >&2
        echo "" >&2
        if [[ "$instance_id" =~ "Free Tier" ]] || [[ "$instance_id" =~ "not eligible" ]]; then
            echo -e "${YELLOW}💡 解決方案：${NC}" >&2
            echo -e "${CYAN}  此實例類型不適用於 Free Tier，請使用以下命令重新執行：${NC}" >&2
            echo -e "${CYAN}  export INSTANCE_TYPE=t3.micro${NC}" >&2
            echo -e "${CYAN}  bash ./deploy-ec2-websites.sh${NC}" >&2
            echo "" >&2
            echo -e "${CYAN}  或使用其他 Free Tier 實例類型：${NC}" >&2
            echo -e "${CYAN}  - t3.micro (推薦)${NC}" >&2
            echo -e "${CYAN}  - t4g.micro (ARM 架構)${NC}" >&2
        fi
        return 1
    fi
    
    echo -e "${GREEN}✅ 實例已啟動: $instance_id${NC}" >&2
    echo -e "${YELLOW}等待實例運行中...${NC}" >&2
    
    # 等待實例運行
    if ! aws ec2 wait instance-running \
        --instance-ids "$instance_id" \
        --region "$REGION" 2>/dev/null; then
        echo -e "${RED}❌ 等待實例運行失敗${NC}" >&2
        return 1
    fi
    
    # 取得公網 IP
    sleep 5  # 等待 IP 分配
    local public_ip
    public_ip=$(aws ec2 describe-instances \
        --instance-ids "$instance_id" \
        --region "$REGION" \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text 2>/dev/null)
    
    if [ -z "$public_ip" ] || [ "$public_ip" = "None" ]; then
        echo -e "${YELLOW}⚠️  無法取得公網 IP，可能實例沒有公網 IP 或還在分配中${NC}" >&2
        public_ip="N/A"
    else
        echo -e "${GREEN}✅ 實例運行中，公網 IP: $public_ip${NC}" >&2
    fi
    
    # 等待 Nginx 啟動（約 30 秒）
    echo -e "${YELLOW}等待網站部署完成（約 30 秒）...${NC}" >&2
    sleep 30
    
    # 測試網站是否可訪問
    if [ "$public_ip" != "N/A" ]; then
        if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "http://$public_ip" 2>/dev/null | grep -q "200"; then
            echo -e "${GREEN}✅ 網站已可訪問: http://$public_ip${NC}" >&2
        else
            echo -e "${YELLOW}⚠️  網站可能還在部署中，請稍後訪問: http://$public_ip${NC}" >&2
        fi
    fi
    
    echo "$instance_id|$public_ip"
    return 0
}

# -------------------------------------------------------------------------------
# 主流程
# -------------------------------------------------------------------------------
main() {
    echo -e "${CYAN}使用實例類型: $INSTANCE_TYPE${NC}"
    echo -e "${YELLOW}💡 提示: 如果此實例類型不適用於 Free Tier，請設定環境變數${NC}"
    echo -e "${YELLOW}   例如: export INSTANCE_TYPE=t3.micro${NC}\n"
    
    # 取得 AMI ID
    if [ -z "$AMI_ID" ]; then
        if [ "$OS_TYPE" = "ubuntu" ]; then
            echo -e "${CYAN}🔍 取得最新的 Ubuntu 22.04 LTS AMI...${NC}"
            AMI_ID=$(get_latest_ubuntu_ami "$REGION")
            if [ -z "$AMI_ID" ] || [ "$AMI_ID" = "None" ]; then
                echo -e "${YELLOW}⚠️  無法取得 Ubuntu AMI，嘗試使用 Amazon Linux 2...${NC}"
                AMI_ID=$(get_latest_amazon_linux_ami "$REGION")
                OS_TYPE="amazon-linux"
            fi
        else
            echo -e "${CYAN}🔍 取得最新的 Amazon Linux 2 AMI...${NC}"
            AMI_ID=$(get_latest_amazon_linux_ami "$REGION")
        fi
        
        if [ -z "$AMI_ID" ] || [ "$AMI_ID" = "None" ]; then
            echo -e "${RED}❌ 無法取得 AMI ID${NC}"
            exit 1
        fi
        echo -e "${GREEN}✅ 使用 AMI: $AMI_ID (OS: $OS_TYPE)${NC}\n"
    fi
    
    # 設定 Key Pair
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}步驟 1: 設定 Key Pair${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    # 執行函數（進度訊息輸出到 stderr，返回值輸出到 stdout）
    if ! KEY_FILE=$(setup_key_pair "$KEY_NAME"); then
        echo -e "${RED}❌ Key Pair 設定失敗${NC}"
        exit 1
    fi
    
    if [ -z "$KEY_FILE" ]; then
        echo -e "${RED}❌ Key Pair 設定失敗：未取得 Key File 路徑${NC}"
        exit 1
    fi
    
    echo ""
    
    # 設定 Security Group
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}步驟 2: 設定 Security Group${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    # 執行函數（進度訊息輸出到 stderr，返回值輸出到 stdout）
    if ! SG_ID=$(setup_security_group "$SECURITY_GROUP_NAME"); then
        echo -e "${RED}❌ Security Group 設定失敗${NC}"
        exit 1
    fi
    
    if [ -z "$SG_ID" ] || [ "$SG_ID" = "None" ]; then
        echo -e "${RED}❌ Security Group 設定失敗：未取得 Security Group ID${NC}"
        exit 1
    fi
    
    echo ""
    
    # 啟動 AWS EC2
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}部署 EC2-1 (AWS)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    AWS_RESULT=$(launch_instance \
        "DNS-Test-AWS" \
        "AWS" \
        "3.3.3.3" \
        "linear-gradient(135deg, #667eea 0%, #764ba2 100%)" \
        "$AMI_ID" \
        "$KEY_NAME" \
        "$SG_ID")
    
    if [ $? -ne 0 ] || [ -z "$AWS_RESULT" ]; then
        echo -e "${RED}❌ AWS EC2 部署失敗${NC}"
        exit 1
    fi
    
    AWS_INSTANCE_ID=$(echo "$AWS_RESULT" | cut -d'|' -f1)
    AWS_PUBLIC_IP=$(echo "$AWS_RESULT" | cut -d'|' -f2)
    
    if [ -z "$AWS_INSTANCE_ID" ] || [ "$AWS_INSTANCE_ID" = "None" ]; then
        echo -e "${RED}❌ 無法取得 AWS EC2 實例 ID${NC}"
        exit 1
    fi
    
    echo ""
    
    # 啟動 Google EC2
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}部署 EC2-2 (Google)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    GCP_RESULT=$(launch_instance \
        "DNS-Test-Google" \
        "Google" \
        "2.2.2.2" \
        "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)" \
        "$AMI_ID" \
        "$KEY_NAME" \
        "$SG_ID")
    
    if [ $? -ne 0 ] || [ -z "$GCP_RESULT" ]; then
        echo -e "${RED}❌ Google EC2 部署失敗${NC}"
        echo -e "${YELLOW}⚠️  已成功部署 AWS EC2: $AWS_INSTANCE_ID${NC}"
        echo -e "${YELLOW}如需清理，執行: aws ec2 terminate-instances --instance-ids $AWS_INSTANCE_ID --region $REGION${NC}"
        exit 1
    fi
    
    GCP_INSTANCE_ID=$(echo "$GCP_RESULT" | cut -d'|' -f1)
    GCP_PUBLIC_IP=$(echo "$GCP_RESULT" | cut -d'|' -f2)
    
    if [ -z "$GCP_INSTANCE_ID" ] || [ "$GCP_INSTANCE_ID" = "None" ]; then
        echo -e "${RED}❌ 無法取得 Google EC2 實例 ID${NC}"
        echo -e "${YELLOW}⚠️  已成功部署 AWS EC2: $AWS_INSTANCE_ID${NC}"
        exit 1
    fi
    
    # 顯示摘要
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ 部署完成！${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    echo -e "${CYAN}📋 實例資訊：${NC}\n"
    
    echo -e "${BLUE}EC2-1 (AWS):${NC}"
    echo -e "  實例 ID: ${CYAN}$AWS_INSTANCE_ID${NC}"
    echo -e "  公網 IP: ${CYAN}$AWS_PUBLIC_IP${NC}"
    echo -e "  網站: ${GREEN}http://$AWS_PUBLIC_IP${NC}"
    echo -e "  應顯示: ${YELLOW}我是 AWS 3.3.3.3${NC}"
    echo ""
    
    echo -e "${BLUE}EC2-2 (Google):${NC}"
    echo -e "  實例 ID: ${CYAN}$GCP_INSTANCE_ID${NC}"
    echo -e "  公網 IP: ${CYAN}$GCP_PUBLIC_IP${NC}"
    echo -e "  網站: ${GREEN}http://$GCP_PUBLIC_IP${NC}"
    echo -e "  應顯示: ${YELLOW}我是 Google 2.2.2.2${NC}"
    echo ""
    
    echo -e "${CYAN}📝 下一步：${NC}"
    echo "1. 在 Route53 建立 A 記錄指向 AWS EC2: $AWS_PUBLIC_IP"
    echo "2. 在 Google Cloud DNS 建立 A 記錄指向 Google EC2: $GCP_PUBLIC_IP"
    echo "3. 執行 DNS failover 測試："
    echo -e "   ${CYAN}sudo bash ./dns-failover-test.sh <域名> $AWS_PUBLIC_IP $GCP_PUBLIC_IP${NC}"
    echo ""
    
    echo -e "${YELLOW}💡 提示：${NC}"
    echo "要刪除實例，執行："
    echo -e "  ${CYAN}aws ec2 terminate-instances --instance-ids $AWS_INSTANCE_ID $GCP_INSTANCE_ID --region $REGION${NC}"
    echo ""
}

main "$@"
