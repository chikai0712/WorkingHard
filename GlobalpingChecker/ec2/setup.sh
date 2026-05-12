#!/bin/bash

# ============================================
# Globalping Checker - EC2 自動安裝腳本
# 適用於 Amazon Linux 2 / Ubuntu
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================"
echo "Globalping Checker - EC2 安裝"
echo "========================================${NC}"
echo ""

# 檢測作業系統
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo -e "${RED}無法檢測作業系統${NC}"
    exit 1
fi

echo -e "${GREEN}檢測到作業系統: $OS${NC}"
echo ""

# 安裝依賴
echo -e "${YELLOW}步驟 1/6: 安裝系統依賴...${NC}"

if [[ "$OS" == "amzn" ]] || [[ "$OS" == "rhel" ]] || [[ "$OS" == "centos" ]]; then
    # Amazon Linux 2 / RHEL / CentOS
    sudo yum update -y
    sudo yum install -y python3 python3-pip curl jq git
elif [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
    # Ubuntu / Debian
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip curl jq git
else
    echo -e "${RED}不支援的作業系統: $OS${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 系統依賴已安裝${NC}"
echo ""

# 安裝 Python 依賴
echo -e "${YELLOW}步驟 2/6: 安裝 Python 依賴...${NC}"
sudo pip3 install requests boto3 --quiet
echo -e "${GREEN}✓ Python 依賴已安裝${NC}"
echo ""

# 創建工作目錄
echo -e "${YELLOW}步驟 3/6: 創建工作目錄...${NC}"
WORK_DIR="/opt/globalping-checker"
sudo mkdir -p "$WORK_DIR"
sudo chown $(whoami):$(whoami) "$WORK_DIR"

# 複製腳本
if [ -d "/home/ec2-user/GlobalpingChecker" ]; then
    cp -r /home/ec2-user/GlobalpingChecker/* "$WORK_DIR/"
elif [ -d "/home/ubuntu/GlobalpingChecker" ]; then
    cp -r /home/ubuntu/GlobalpingChecker/* "$WORK_DIR/"
else
    echo -e "${YELLOW}未找到本地腳本，將從當前目錄複製${NC}"
    cp -r ../*.sh "$WORK_DIR/" 2>/dev/null || true
fi

echo -e "${GREEN}✓ 工作目錄已創建: $WORK_DIR${NC}"
echo ""

# 創建日誌目錄
echo -e "${YELLOW}步驟 4/6: 創建日誌目錄...${NC}"
LOG_DIR="/var/log/globalping-checker"
sudo mkdir -p "$LOG_DIR"
sudo chown $(whoami):$(whoami) "$LOG_DIR"
echo -e "${GREEN}✓ 日誌目錄: $LOG_DIR${NC}"
echo ""

# 創建配置文件
echo -e "${YELLOW}步驟 5/6: 創建配置文件...${NC}"

cat > "$WORK_DIR/config.env" << 'EOF'
# Globalping Checker 配置文件

# Globalping API Token (可選)
GLOBALPING_TOKEN=""

# 域名文件路徑
DOMAINS_FILE="/opt/globalping-checker/domains.txt"

# 日誌目錄
LOG_DIR="/var/log/globalping-checker"

# S3 Bucket (可選，用於備份結果)
S3_BUCKET=""

# 通知 Email (可選)
NOTIFICATION_EMAIL=""

# 執行排程 (cron 格式)
# 預設: 每天凌晨 2 點
CRON_SCHEDULE="0 2 * * *"
EOF

echo -e "${GREEN}✓ 配置文件已創建: $WORK_DIR/config.env${NC}"
echo ""

# 創建執行腳本
echo -e "${YELLOW}步驟 6/6: 創建執行腳本...${NC}"

cat > "$WORK_DIR/run_check.sh" << 'EOFSCRIPT'
#!/bin/bash

# 載入配置
source /opt/globalping-checker/config.env

# 設置日誌文件
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/check_${TIMESTAMP}.log"

echo "========================================" | tee -a "$LOG_FILE"
echo "開始執行域名檢測 - $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 檢查域名文件
if [ ! -f "$DOMAINS_FILE" ]; then
    echo "錯誤: 域名文件不存在: $DOMAINS_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

# 執行檢測（使用 v3.1 Token 版本）
cd /opt/globalping-checker

if [ -f "id_globalping_multi_v3.1_Token.sh" ]; then
    # 設置 Token
    if [ -n "$GLOBALPING_TOKEN" ]; then
        export GLOBALPING_TOKEN
    fi
    
    # 執行檢測
    ./id_globalping_multi_v3.1_Token.sh "$DOMAINS_FILE" 2>&1 | tee -a "$LOG_FILE"
elif [ -f "id_globalping_multi_v3.0.sh" ]; then
    ./id_globalping_multi_v3.0.sh "$DOMAINS_FILE" 2>&1 | tee -a "$LOG_FILE"
else
    echo "錯誤: 找不到檢測腳本" | tee -a "$LOG_FILE"
    exit 1
fi

# 備份到 S3 (如果配置了)
if [ -n "$S3_BUCKET" ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "上傳結果到 S3..." | tee -a "$LOG_FILE"
    
    # 上傳日誌
    aws s3 cp "$LOG_FILE" "s3://$S3_BUCKET/logs/" 2>&1 | tee -a "$LOG_FILE"
    
    # 上傳最新的 globalping 日誌
    LATEST_LOG=$(ls -t ~/globalping_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        aws s3 cp "$LATEST_LOG" "s3://$S3_BUCKET/results/" 2>&1 | tee -a "$LOG_FILE"
    fi
    
    echo "✓ 結果已上傳到 S3" | tee -a "$LOG_FILE"
fi

# 發送通知 (如果配置了)
if [ -n "$NOTIFICATION_EMAIL" ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "發送通知到 $NOTIFICATION_EMAIL..." | tee -a "$LOG_FILE"
    
    # 提取摘要
    SUMMARY=$(tail -20 "$LOG_FILE" | grep -A 10 "檢測完成")
    
    # 使用 AWS SES 發送 (需要配置 SES)
    if command -v aws &> /dev/null; then
        echo "$SUMMARY" | aws ses send-email \
            --from "noreply@yourdomain.com" \
            --to "$NOTIFICATION_EMAIL" \
            --subject "Globalping 檢測報告 - $(date +%Y-%m-%d)" \
            --text "$SUMMARY" 2>&1 | tee -a "$LOG_FILE" || true
    fi
fi

echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "檢測完成 - $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 清理舊日誌 (保留 30 天)
find "$LOG_DIR" -name "check_*.log" -mtime +30 -delete 2>/dev/null || true
EOFSCRIPT

chmod +x "$WORK_DIR/run_check.sh"

echo -e "${GREEN}✓ 執行腳本已創建: $WORK_DIR/run_check.sh${NC}"
echo ""

# 設置 Cron
echo -e "${YELLOW}是否要設置定時任務? (y/N): ${NC}"
read -r SETUP_CRON

if [[ "$SETUP_CRON" =~ ^[Yy]$ ]]; then
    # 讀取 cron 排程
    source "$WORK_DIR/config.env"
    
    # 添加到 crontab
    (crontab -l 2>/dev/null | grep -v "globalping-checker"; echo "$CRON_SCHEDULE $WORK_DIR/run_check.sh") | crontab -
    
    echo -e "${GREEN}✓ 定時任務已設置: $CRON_SCHEDULE${NC}"
    echo ""
    echo "查看定時任務:"
    crontab -l | grep globalping
else
    echo -e "${YELLOW}跳過定時任務設置${NC}"
fi

echo ""
echo -e "${BLUE}========================================"
echo "安裝完成！"
echo "========================================${NC}"
echo ""
echo -e "${GREEN}工作目錄:${NC} $WORK_DIR"
echo -e "${GREEN}日誌目錄:${NC} $LOG_DIR"
echo -e "${GREEN}配置文件:${NC} $WORK_DIR/config.env"
echo ""
echo -e "${BLUE}下一步操作:${NC}"
echo ""
echo "1. 編輯配置文件:"
echo -e "   ${YELLOW}nano $WORK_DIR/config.env${NC}"
echo ""
echo "2. 上傳域名列表:"
echo -e "   ${YELLOW}nano $WORK_DIR/domains.txt${NC}"
echo ""
echo "3. 手動執行測試:"
echo -e "   ${YELLOW}$WORK_DIR/run_check.sh${NC}"
echo ""
echo "4. 查看日誌:"
echo -e "   ${YELLOW}tail -f $LOG_DIR/check_*.log${NC}"
echo ""
echo "5. 設置定時任務 (如果還沒設置):"
echo -e "   ${YELLOW}crontab -e${NC}"
echo -e "   添加: ${YELLOW}0 2 * * * $WORK_DIR/run_check.sh${NC}"
echo ""
echo -e "${GREEN}安裝成功！ 🎉${NC}"
