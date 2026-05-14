#!/bin/bash

# 快速測試 Telegram Bot
# 使用你的 Bot Token 發送測試消息

BOT_TOKEN="8771241397:AAEsXT-Cn5EQ6sRBiHar1AKKwiQPKxJ_dJo"

echo "🧪 Telegram Bot 測試工具"
echo "========================================"
echo ""

# 檢查 Bot 資訊
echo "1️⃣  檢查 Bot 資訊..."
BOT_INFO=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getMe")

if echo "$BOT_INFO" | grep -q '"ok":true'; then
    echo "✅ Bot Token 有效"
    BOT_NAME=$(echo "$BOT_INFO" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
    echo "   Bot 用戶名: @$BOT_NAME"
else
    echo "❌ Bot Token 無效"
    exit 1
fi

echo ""
echo "2️⃣  獲取 Chat ID..."
echo ""
echo "請按照以下步驟操作："
echo ""
echo "方法 1：使用 @userinfobot（推薦）"
echo "  1. 在 Telegram 搜尋 @userinfobot"
echo "  2. 發送任意消息"
echo "  3. 複製你的 ID"
echo ""
echo "方法 2：向你的 Bot 發送消息"
echo "  1. 在 Telegram 搜尋 @$BOT_NAME"
echo "  2. 點擊 START 或發送 /start"
echo "  3. 訪問以下網址獲取 Chat ID："
echo "     https://api.telegram.org/bot${BOT_TOKEN}/getUpdates"
echo ""

read -p "已獲取 Chat ID? 輸入你的 Chat ID: " CHAT_ID

if [ -z "$CHAT_ID" ]; then
    echo "❌ Chat ID 不能為空"
    exit 1
fi

echo ""
echo "3️⃣  發送測試消息..."

TEST_MESSAGE="✅ *Telegram Bot 測試成功！*

你的 Bot 已正確配置。

Bot: @$BOT_NAME
Chat ID: \`$CHAT_ID\`
時間: \`$(date '+%Y-%m-%d %H:%M:%S')\`

現在可以開始使用 Globalping Checker 的 Telegram 通知功能了！"

RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d "chat_id=$CHAT_ID" \
    -d "text=$TEST_MESSAGE" \
    -d "parse_mode=Markdown")

if echo "$RESPONSE" | grep -q '"ok":true'; then
    echo "✅ 測試消息已發送！"
    echo "   請檢查 Telegram 是否收到消息"
    echo ""
    echo "========================================"
    echo "✅ 配置成功"
    echo "========================================"
    echo ""
    echo "你的配置資訊："
    echo "  Bot Token: $BOT_TOKEN"
    echo "  Chat ID: $CHAT_ID"
    echo ""
    echo "下一步："
    echo "  1. 執行: bash setup-telegram.sh"
    echo "  2. 輸入上述 Bot Token 和 Chat ID"
    echo "  3. 測試: bash id_globalping_multi_v3.3_Telegram.sh test_2_domains.txt"
else
    echo "❌ 發送失敗"
    echo "   錯誤: $RESPONSE"
    echo ""
    echo "請檢查："
    echo "  1. Chat ID 是否正確"
    echo "  2. 是否已向 Bot 發送過消息"
fi

echo ""
