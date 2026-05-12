#!/bin/bash

# V4.1 手動更新 AWS 腳本
# 使用方法：在 AWS EC2 終端機上執行此腳本

set -e  # 遇到錯誤立即停止

echo "========================================"
echo "🚀 GlobalpingChecker V4.1 更新腳本"
echo "========================================"
echo ""

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
PROJECT_DIR="$HOME/globalping-v4.1"
BACKUP_DIR="$HOME/globalping-v4.1-backup-$(date +%Y%m%d-%H%M%S)"

echo -e "${YELLOW}步驟 1/6: 檢查環境${NC}"
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ 找不到項目目錄: $PROJECT_DIR${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 項目目錄存在${NC}"
echo ""

echo -e "${YELLOW}步驟 2/6: 備份當前版本${NC}"
echo "備份到: $BACKUP_DIR"
cp -r "$PROJECT_DIR" "$BACKUP_DIR"
echo -e "${GREEN}✅ 備份完成${NC}"
echo ""

echo -e "${YELLOW}步驟 3/6: 停止服務${NC}"
cd "$PROJECT_DIR"
docker-compose down
echo -e "${GREEN}✅ 服務已停止${NC}"
echo ""

echo -e "${YELLOW}步驟 4/6: 更新代碼${NC}"

# 更新 app/ 目錄
echo "更新 app/ 目錄..."
cat > "$PROJECT_DIR/app/config.py" << 'EOF'
"""
GlobalpingChecker V4.1 - Configuration
"""
from functools import lru_cache
from typing import ClassVar
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./data/globalping_results.db"
    
    # Globalping API
    globalping_api_url: str = "https://api.globalping.io/v1"
    globalping_token: str = ""
    
    # Target Countries Switches (國家開關)
    enable_indonesia: bool = True
    enable_vietnam: bool = False
    enable_thailand: bool = False
    
    # 國家映射 (使用 ClassVar 避免 Pydantic 錯誤)
    COUNTRY_MAP: ClassVar[dict] = {
        "indonesia": {"code": "ID", "name": "Indonesia"},
        "vietnam": {"code": "VN", "name": "Vietnam"},
        "thailand": {"code": "TH", "name": "Thailand"}
    }
    
    @property
    def target_country_list(self) -> list:
        """根據開關返回啟用的國家代碼列表"""
        countries = []
        if self.enable_indonesia:
            countries.append(self.COUNTRY_MAP["indonesia"]["code"])
        if self.enable_vietnam:
            countries.append(self.COUNTRY_MAP["vietnam"]["code"])
        if self.enable_thailand:
            countries.append(self.COUNTRY_MAP["thailand"]["code"])
        
        # 如果沒有啟用任何國家，默認啟用印尼
        if not countries:
            countries.append("ID")
        
        return countries
    
    @property
    def target_country_name_list(self) -> list:
        """根據開關返回啟用的國家名稱列表"""
        names = []
        if self.enable_indonesia:
            names.append(self.COUNTRY_MAP["indonesia"]["name"])
        if self.enable_vietnam:
            names.append(self.COUNTRY_MAP["vietnam"]["name"])
        if self.enable_thailand:
            names.append(self.COUNTRY_MAP["thailand"]["name"])
        
        # 如果沒有啟用任何國家，默認啟用印尼
        if not names:
            names.append("Indonesia")
        
        return names
    
    # Scheduler
    check_interval_minutes: int = 90
    abnormal_check_hour: int = 1      # AM 1:00
    normal_check_hour: int = 9        # AM 9:00
    max_iterations: int = 10          # 第一循環最大檢測次數
    
    # Domains
    domains_file: str = "domains.txt"
    
    # Web Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
EOF

# 更新 .env
echo "更新 .env 配置..."
cat > "$PROJECT_DIR/.env" << 'EOF'
# Database
DATABASE_URL=sqlite:///./data/globalping_results.db

# Globalping API
GLOBALPING_API_URL=https://api.globalping.io/v1
GLOBALPING_TOKEN=uh5vlg4ttg3v5gwby5zgtqrciimahql5

# Target Country (目標檢測國家)
# 國家開關：設置為 true 啟用，false 停用
ENABLE_INDONESIA=true
ENABLE_VIETNAM=false
ENABLE_THAILAND=false

# Scheduler Settings
CHECK_INTERVAL_MINUTES=90
ABNORMAL_CHECK_HOUR=1
NORMAL_CHECK_HOUR=9
MAX_ITERATIONS=10

# Domain List
DOMAINS_FILE=domains.txt

# Server
HOST=0.0.0.0
PORT=8000
EOF

echo -e "${GREEN}✅ 代碼更新完成${NC}"
echo ""

echo -e "${YELLOW}步驟 5/6: 重新構建並啟動服務${NC}"
docker-compose build
docker-compose up -d
echo -e "${GREEN}✅ 服務已啟動${NC}"
echo ""

echo -e "${YELLOW}步驟 6/6: 等待服務啟動並檢查狀態${NC}"
sleep 5
docker-compose ps
echo ""

echo -e "${GREEN}========================================"
echo "✅ 更新完成！"
echo "========================================${NC}"
echo ""
echo "📊 查看日誌："
echo "   docker-compose logs -f --tail=50"
echo ""
echo "🌐 訪問服務："
echo "   http://54.238.247.106:8000"
echo ""
echo "💾 備份位置："
echo "   $BACKUP_DIR"
echo ""
