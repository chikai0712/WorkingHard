#!/bin/bash
# ============================================
# 測試密碼提示腳本
# 用於驗證密碼輸入提示是否清晰
# ============================================

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "=========================================="
echo "測試密碼提示"
echo "=========================================="
echo ""
echo "此腳本將測試 sudo 密碼輸入提示"
echo ""

# 檢查 sudo 權限
echo "檢查 sudo 權限..."
if sudo -v 2>/dev/null; then
    echo -e "${GREEN}✅ sudo 權限已緩存${NC}"
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${YELLOW}⚠️  需要輸入密碼以獲取 sudo 權限${NC}"
    echo ""
    echo -e "${BLUE}請在下方輸入您的 macOS 用戶密碼：${NC}"
    echo "  （輸入時不會顯示，這是正常的安全機制）"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    if sudo -v; then
        echo ""
        echo -e "${GREEN}✅ sudo 權限已獲取並緩存${NC}"
    else
        echo ""
        echo -e "${RED}❌ 無法獲取 sudo 權限${NC}"
        exit 1
    fi
fi

echo ""
echo "測試完成！"

