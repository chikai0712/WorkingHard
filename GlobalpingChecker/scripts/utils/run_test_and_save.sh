#!/bin/bash

# ============================================
# 域名檢測 + 數據庫保存一體化腳本
# 功能：
# 1. 執行 v3.1_Token 域名檢測
# 2. 自動保存結果到 SQLite 數據庫
# 3. 顯示測試摘要
# 4. 導出 CSV 文件
# ============================================

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_SCRIPT="$SCRIPT_DIR/id_globalping_multi_v3.1_Token.sh"
SAVE_SCRIPT="$SCRIPT_DIR/save_to_db.py"
VIEW_SCRIPT="$SCRIPT_DIR/view_db.py"
DB_FILE="$SCRIPT_DIR/globalping_results.db"

# 檢查參數
if [ $# -lt 1 ]; then
    echo "用法: $0 <域名文件> [備註]"
    echo ""
    echo "範例："
    echo "  $0 test_2_domains.txt"
    echo "  $0 test_10_domains.txt '每日定時檢測'"
    echo "  $0 domains.txt '完整測試 - 2026-03-06'"
    exit 1
fi

DOMAINS_FILE="$1"
NOTES="${2:-}"

# 檢查文件是否存在
if [ ! -f "$DOMAINS_FILE" ]; then
    echo -e "${RED}❌ 錯誤：找不到域名文件 $DOMAINS_FILE${NC}"
    exit 1
fi

if [ ! -f "$TEST_SCRIPT" ]; then
    echo -e "${RED}❌ 錯誤：找不到測試腳本 $TEST_SCRIPT${NC}"
    exit 1
fi

if [ ! -f "$SAVE_SCRIPT" ]; then
    echo -e "${RED}❌ 錯誤：找不到數據庫保存腳本 $SAVE_SCRIPT${NC}"
    exit 1
fi

# 確保腳本可執行
chmod +x "$TEST_SCRIPT"

echo -e "${BLUE}========================================"
echo "域名檢測 + 數據庫保存"
echo "========================================${NC}"
echo "域名文件: $DOMAINS_FILE"
echo "數據庫: $DB_FILE"
if [ -n "$NOTES" ]; then
    echo "備註: $NOTES"
fi
echo ""

# 步驟 1：執行域名檢測
echo -e "${GREEN}📡 步驟 1/4: 執行域名檢測...${NC}"
echo ""

"$TEST_SCRIPT" "$DOMAINS_FILE"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 域名檢測失敗${NC}"
    exit 1
fi

# 找到最新的日誌文件
LOG_FILE=$(ls -t ~/globalping_*.log 2>/dev/null | head -1)

if [ -z "$LOG_FILE" ] || [ ! -f "$LOG_FILE" ]; then
    echo -e "${RED}❌ 找不到測試日誌文件${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ 檢測完成，日誌文件: $LOG_FILE${NC}"
echo ""

# 步驟 2：保存到數據庫
echo -e "${GREEN}💾 步驟 2/4: 保存結果到數據庫...${NC}"
echo ""

if [ -n "$NOTES" ]; then
    python3 "$SAVE_SCRIPT" "$LOG_FILE" "$NOTES"
else
    python3 "$SAVE_SCRIPT" "$LOG_FILE"
fi

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 數據庫保存失敗${NC}"
    exit 1
fi

echo ""

# 步驟 3：顯示統計信息
echo -e "${GREEN}📊 步驟 3/4: 顯示統計信息...${NC}"
echo ""

# 獲取最新的批次 ID
BATCH_ID=$(sqlite3 "$DB_FILE" "SELECT batch_id FROM test_batches ORDER BY batch_id DESC LIMIT 1" 2>/dev/null)

if [ -n "$BATCH_ID" ]; then
    python3 "$VIEW_SCRIPT" --db "$DB_FILE" stats --batch "$BATCH_ID"
fi

echo ""

# 步驟 4：生成快速查看命令
echo -e "${GREEN}📋 步驟 4/4: 完成！${NC}"
echo ""
echo "=========================================="
echo "✅ 所有步驟完成"
echo "=========================================="
echo ""
echo "📊 數據庫文件: $DB_FILE"
echo "📄 日誌文件: $LOG_FILE"
if [ -n "$BATCH_ID" ]; then
    echo "🆔 批次 ID: $BATCH_ID"
    CSV_FILE="test_results_batch_${BATCH_ID}.csv"
    if [ -f "$CSV_FILE" ]; then
        echo "📊 CSV 文件: $CSV_FILE"
    fi
fi
echo ""
echo "常用查詢命令："
echo "  # 查看所有測試批次"
echo "  python3 $VIEW_SCRIPT list"
echo ""
if [ -n "$BATCH_ID" ]; then
    echo "  # 查看本次測試詳情"
    echo "  python3 $VIEW_SCRIPT show $BATCH_ID"
    echo ""
fi
echo "  # 查看統計信息"
echo "  python3 $VIEW_SCRIPT stats"
echo ""
echo "  # 查詢特定域名"
echo "  python3 $VIEW_SCRIPT domain <域名>"
echo ""
echo "=========================================="
