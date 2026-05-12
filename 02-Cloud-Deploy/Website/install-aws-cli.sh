#!/bin/bash

# AWS CLI 自動安裝腳本（macOS）

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📦 AWS CLI 安裝助手${NC}"
echo ""

# 檢查作業系統
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo -e "${GREEN}偵測到系統：${MACHINE}${NC}"
echo ""

# macOS 安裝
if [ "$MACHINE" == "Mac" ]; then
    # 檢查是否已安裝
    if command -v aws &> /dev/null; then
        echo -e "${GREEN}✅ AWS CLI 已安裝${NC}"
        aws --version
        echo ""
        read -p "要重新安裝嗎？(y/n): " reinstall
        if [ "$reinstall" != "y" ] && [ "$reinstall" != "Y" ]; then
            exit 0
        fi
    fi
    
    # 檢查 Homebrew
    if command -v brew &> /dev/null; then
        echo -e "${GREEN}📦 使用 Homebrew 安裝...${NC}"
        brew install awscli
    else
        echo -e "${YELLOW}⚠️  Homebrew 未安裝${NC}"
        echo ""
        read -p "要安裝 Homebrew 嗎？(y/n): " install_brew
        
        if [ "$install_brew" == "y" ] || [ "$install_brew" == "Y" ]; then
            echo -e "${GREEN}📦 安裝 Homebrew...${NC}"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            
            echo -e "${GREEN}📦 安裝 AWS CLI...${NC}"
            brew install awscli
        else
            echo -e "${YELLOW}使用安裝程式方式...${NC}"
            echo "請手動下載並安裝："
            echo "  https://awscli.amazonaws.com/AWSCLIV2.pkg"
            exit 0
        fi
    fi

# Linux 安裝
elif [ "$MACHINE" == "Linux" ]; then
    echo -e "${GREEN}📦 下載 AWS CLI...${NC}"
    
    cd /tmp
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip -q awscliv2.zip
    
    echo -e "${GREEN}📦 安裝 AWS CLI...${NC}"
    sudo ./aws/install
    
    rm -rf aws awscliv2.zip
    
else
    echo -e "${RED}❌ 不支援的作業系統${NC}"
    exit 1
fi

# 驗證安裝
echo ""
echo -e "${GREEN}✅ 驗證安裝...${NC}"
if aws --version; then
    echo ""
    echo -e "${GREEN}✅ AWS CLI 安裝成功！${NC}"
    echo ""
    echo -e "${YELLOW}下一步：${NC}"
    echo "  1. 配置 AWS 憑證："
    echo "     aws configure"
    echo ""
    echo "  2. 執行設定腳本："
    echo "     cd Website"
    echo "     ./setup-aws-key.sh"
else
    echo -e "${RED}❌ 安裝失敗${NC}"
    exit 1
fi
