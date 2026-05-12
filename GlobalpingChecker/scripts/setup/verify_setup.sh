#!/bin/bash

# ============================================
# 功能驗證測試腳本
# 自動測試所有數據庫功能
# ============================================

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================"
echo "功能驗證測試"
echo "========================================${NC}"
echo ""

# 測試計數
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 測試函數
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${YELLOW}測試 $TOTAL_TESTS: $test_name${NC}"
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 通過${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}❌ 失敗${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

echo -e "${BLUE}=== 階段 1: 檢查文件存在 ===${NC}"
echo ""

run_test "檢查 v3.1_Token 腳本" "test -f id_globalping_multi_v3.1_Token.sh"
run_test "檢查 run_test_and_save 腳本" "test -f run_test_and_save.sh"
run_test "檢查 save_to_db.py" "test -f save_to_db.py"
run_test "檢查 view_db.py" "test -f view_db.py"
run_test "檢查測試域名文件" "test -f test_2_domains.txt"
run_test "檢查 DATABASE_GUIDE.md" "test -f DATABASE_GUIDE.md"
run_test "檢查 DATABASE_QUICKSTART.md" "test -f DATABASE_QUICKSTART.md"

echo ""
echo -e "${BLUE}=== 階段 2: 檢查腳本權限 ===${NC}"
echo ""

run_test "v3.1_Token 腳本可執行" "test -x id_globalping_multi_v3.1_Token.sh"
run_test "run_test_and_save 腳本可執行" "test -x run_test_and_save.sh"

echo ""
echo -e "${BLUE}=== 階段 3: 檢查 Python 依賴 ===${NC}"
echo ""

run_test "Python3 已安裝" "which python3"
run_test "SQLite3 模塊可用" "python3 -c 'import sqlite3'"

echo ""
echo -e "${BLUE}=== 階段 4: 檢查 Token 有效性 ===${NC}"
echo ""

echo -e "${YELLOW}測試 Token 認證...${NC}"
TOKEN_RESPONSE=$(curl -s -H "Authorization: Bearer uh5vlg4ttg3v5gwby5zgtqrciimahql5" \
  https://api.globalping.io/v1/limits)

if echo "$TOKEN_RESPONSE" | grep -q '"type":"user"'; then
    echo -e "${GREEN}✅ Token 有效（註冊使用者）${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    
    # 顯示配額信息
    LIMIT=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['rateLimit']['measurements']['create']['limit'])" 2>/dev/null || echo "N/A")
    REMAINING=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['rateLimit']['measurements']['create']['remaining'])" 2>/dev/null || echo "N/A")
    echo "  配額: $LIMIT/小時"
    echo "  剩餘: $REMAINING"
else
    echo -e "${RED}❌ Token 無效${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""
echo -e "${BLUE}=== 階段 5: 檢查腳本語法 ===${NC}"
echo ""

run_test "v3.1_Token 腳本語法" "bash -n id_globalping_multi_v3.1_Token.sh"
run_test "run_test_and_save 腳本語法" "bash -n run_test_and_save.sh"
run_test "save_to_db.py 語法" "python3 -m py_compile save_to_db.py"
run_test "view_db.py 語法" "python3 -m py_compile view_db.py"

echo ""
echo -e "${BLUE}=== 階段 6: 測試數據庫初始化 ===${NC}"
echo ""

# 備份現有數據庫（如果存在）
if [ -f "globalping_results.db" ]; then
    echo "備份現有數據庫..."
    cp globalping_results.db "globalping_results.db.backup.$(date +%Y%m%d_%H%M%S)"
fi

echo -e "${YELLOW}測試數據庫初始化...${NC}"
if python3 -c "from save_to_db import GlobalpingDB; db = GlobalpingDB('test_verification.db'); db.close()" 2>/dev/null; then
    echo -e "${GREEN}✅ 數據庫初始化成功${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    rm -f test_verification.db
else
    echo -e "${RED}❌ 數據庫初始化失敗${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""
echo -e "${BLUE}=== 測試總結 ===${NC}"
echo ""
echo "總測試數: $TOTAL_TESTS"
echo -e "${GREEN}通過: $PASSED_TESTS${NC}"
echo -e "${RED}失敗: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ 所有測試通過！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "系統已就緒，可以開始使用："
    echo ""
    echo "  # 執行測試並保存到數據庫"
    echo "  ./run_test_and_save.sh test_2_domains.txt \"第一次測試\""
    echo ""
    echo "  # 查看測試結果"
    echo "  python3 view_db.py list"
    echo ""
    exit 0
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}⚠️  有 $FAILED_TESTS 個測試失敗${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "請檢查失敗的測試項目並修復問題"
    exit 1
fi
