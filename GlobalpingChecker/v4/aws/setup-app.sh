#!/bin/bash

# GlobalpingChecker V4 - 應用程式部署腳本
# 在 EC2 實例上執行

set -e

# 顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

APP_DIR="/opt/globalping"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GlobalpingChecker V4 - 應用程式部署${NC}"
echo -e "${GREEN}========================================${NC}"

# 確保在正確的目錄
cd "$APP_DIR"

# 檢查 .env 文件
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env 文件不存在，請先執行 CloudFormation 部署${NC}"
    exit 1
fi

# 創建應用程式結構
echo -e "${GREEN}📁 創建應用程式結構...${NC}"
mkdir -p app templates static

# 下載或複製應用程式代碼
# 這裡假設代碼已經通過 SCP 或 Git 傳輸到服務器
echo -e "${YELLOW}⚠️  請確保應用程式代碼已複製到 $APP_DIR${NC}"

# 檢查必要文件
REQUIRED_FILES=("app/main.py" "app/database.py" "app/checker.py" "app/scheduler.py" "requirements.txt" "Dockerfile" "docker-compose.yml")

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ 缺少文件: $file${NC}"
        echo -e "${YELLOW}請使用 SCP 複製應用程式代碼：${NC}"
        echo -e "scp -i your-key.pem -r v4/* ec2-user@<IP>:$APP_DIR/"
        exit 1
    fi
done

echo -e "${GREEN}✅ 所有必要文件已就緒${NC}"

# 檢查 domains.txt
if [ ! -f "domains.txt" ]; then
    echo -e "${YELLOW}⚠️  domains.txt 不存在，創建範例文件...${NC}"
    cat > domains.txt << 'EOF'
# GlobalpingChecker V4 - 域名列表
# 每行一個域名，# 開頭為註釋

example.com
google.com
EOF
    echo -e "${GREEN}✅ 已創建範例 domains.txt，請編輯添加實際域名${NC}"
fi

# 啟動 Docker Compose
echo -e "\n${GREEN}🐳 啟動 Docker Compose...${NC}"
docker-compose up -d

# 等待服務啟動
echo -e "${YELLOW}⏳ 等待服務啟動...${NC}"
sleep 10

# 檢查服務狀態
echo -e "\n${GREEN}📊 服務狀態：${NC}"
docker-compose ps

# 檢查健康狀態
echo -e "\n${GREEN}🏥 健康檢查：${NC}"
if curl -s http://localhost:8000/api/stats > /dev/null; then
    echo -e "${GREEN}✅ Web 服務正常運行${NC}"
else
    echo -e "${RED}❌ Web 服務未就緒，請檢查日誌${NC}"
    docker-compose logs web
fi

# 顯示訪問信息
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Dashboard: ${YELLOW}http://$PUBLIC_IP:8000${NC}"
echo -e "API 文檔: ${YELLOW}http://$PUBLIC_IP:8000/docs${NC}"
echo -e "\n${GREEN}常用命令：${NC}"
echo -e "  查看日誌: docker-compose logs -f"
echo -e "  重啟服務: docker-compose restart"
echo -e "  停止服務: docker-compose down"
echo -e "  手動檢測: curl -X POST http://localhost:8000/api/check/trigger"
