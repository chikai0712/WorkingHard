#!/bin/bash

# Telegram 通知配置腳本

echo "🔧 配置 Telegram 通知..."
echo ""

# 檢查是否已有配置
CONFIG_FILE="telegram-config.env"

if [ -f "$CONFIG_FILE" ]; then
    echo "⚠️  已存在 Telegram 配置"
    read -p "是否要重新配置? (y/N): " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        echo "取消配置"
        exit 0
    fi
fi

echo "請提供 Telegram Bot Token 和 Chat ID"
echo ""
echo "如何獲取："
echo ""
echo "1. 創建 Bot Token："
echo "   - 在 Telegram 搜尋 @BotFather"
echo "   - 發送 /newbot"
echo "   - 按提示設置 Bot 名稱"
echo "   - 複製 Bot Token（格式：123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11）"
echo ""
echo "2. 獲取 Chat ID："
echo "   - 在 Telegram 搜尋你的 Bot"
echo "   - 發送任意消息給 Bot"
echo "   - 訪問：https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
echo "   - 找到 \"chat\":{\"id\":123456789}"
echo "   - 或使用 @userinfobot 獲取你的 Chat ID"
echo ""

read -p "輸入 Bot Token: " BOT_TOKEN

if [ -z "$BOT_TOKEN" ]; then
    echo "❌ Bot Token 不能為空"
    exit 1
fi

read -p "輸入 Chat ID: " CHAT_ID

if [ -z "$CHAT_ID" ]; then
    echo "❌ Chat ID 不能為空"
    exit 1
fi

echo ""
read -p "輸入 Bot 名稱（可選，例如: Globalping Checker）: " BOT_NAME

# 創建配置文件
cat > "$CONFIG_FILE" << EOF
# Telegram 通知配置

# Bot Token（必填）
TELEGRAM_BOT_TOKEN="$BOT_TOKEN"

# Chat ID（必填）
TELEGRAM_CHAT_ID="$CHAT_ID"

# Bot 名稱（可選）
TELEGRAM_BOT_NAME="${BOT_NAME:-Globalping Checker}"

# 通知級別
# all: 所有檢測都通知
# errors: 只通知錯誤（BLOCKED, TIMEOUT, WARNING, PARTIAL, API_ERROR）
# critical: 只通知嚴重錯誤（BLOCKED, API_ERROR）
TELEGRAM_NOTIFY_LEVEL="errors"

# 是否啟用通知
TELEGRAM_ENABLED="true"

# 是否使用 Markdown 格式
TELEGRAM_USE_MARKDOWN="true"
EOF

echo ""
echo "✅ 配置已保存到 $CONFIG_FILE"
echo ""

# 測試通知
echo "🧪 測試 Telegram 通知..."
echo ""

TEST_MESSAGE="✅ *Globalping Checker 測試通知*

Telegram 通知已成功配置！

從現在開始，域名檢測結果會自動發送到此聊天。

配置時間: $(date '+%Y-%m-%d %H:%M:%S')"

API_URL="https://api.telegram.org/bot${BOT_TOKEN}/sendMessage"

RESPONSE=$(curl -s -X POST "$API_URL" \
    -d "chat_id=$CHAT_ID" \
    -d "text=$TEST_MESSAGE" \
    -d "parse_mode=Markdown")

if echo "$RESPONSE" | grep -q '"ok":true'; then
    echo ""
    echo "✅ 測試通知已發送！"
    echo "   請檢查 Telegram 是否收到測試消息"
else
    echo ""
    echo "❌ 測試通知發送失敗"
    echo "   錯誤信息: $RESPONSE"
    echo ""
    echo "   請檢查："
    echo "   1. Bot Token 是否正確"
    echo "   2. Chat ID 是否正確"
    echo "   3. 是否已向 Bot 發送過消息"
fi

echo ""
echo "========================================"
echo "配置完成"
echo "========================================"
echo ""
echo "配置文件: $CONFIG_FILE"
echo ""
echo "下一步："
echo "  1. 測試通知:"
echo "     ./id_globalping_multi_v3.2_Telegram.sh test_2_domains.txt"
echo ""
echo "  2. 部署到 EC2:"
echo "     scp $CONFIG_FILE ec2-user@YOUR_IP:/tmp/"
echo "     ssh ec2-user@YOUR_IP 'sudo mv /tmp/$CONFIG_FILE /opt/globalping-checker/'"
echo ""
