#!/bin/bash
# 在系統終端機（iTerm / Terminal.app）執行此腳本
# 繞過 Cursor proxy，直接測試 Telegram 推播

BOT_TOKEN="8771241397:AAESXT-Cn5EQ6sRBiHar1AKKwiQPKxJ_dJo"
CHAT_ID="229891358"

echo "🧪 台指期監控系統 — Telegram 推播測試"
echo "========================================"

# 清除所有 proxy（避免被 Cursor 沙盒干擾）
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
unset ALL_PROXY all_proxy SOCKS_PROXY SOCKS5_PROXY
unset socks_proxy socks5_proxy

echo ""
echo "1️⃣  確認 Bot Token 有效..."
BOT_INFO=$(curl -s --max-time 10 "https://api.telegram.org/bot${BOT_TOKEN}/getMe")
if echo "$BOT_INFO" | grep -q '"ok":true'; then
    BOT_NAME=$(echo "$BOT_INFO" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['username'])")
    echo "✅ Bot Token 有效 — @${BOT_NAME}"
else
    echo "❌ Bot Token 無效：$BOT_INFO"
    exit 1
fi

echo ""
echo "2️⃣  發送基本測試訊息..."
RESP=$(curl -s --max-time 10 -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -H 'Content-Type: application/json' \
    -d "{
        \"chat_id\": \"${CHAT_ID}\",
        \"text\": \"🧪 <b>台指期監控系統 Mock 測試</b>\\n\\n基本推播驗證成功！\\n時間：$(date '+%Y-%m-%d %H:%M:%S')\",
        \"parse_mode\": \"HTML\"
    }")

if echo "$RESP" | grep -q '"ok":true'; then
    echo "✅ 基本訊息推播成功！"
else
    echo "❌ 推播失敗：$RESP"
    exit 1
fi

echo ""
echo "3️⃣  發送警示格式測試..."
RESP2=$(curl -s --max-time 10 -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -H 'Content-Type: application/json' \
    -d "{
        \"chat_id\": \"${CHAT_ID}\",
        \"text\": \"🔴 <b>台指期警示</b>\\n────────────────────\\n📌 <b>MACD 黃金交叉</b>\\n📝 MACD 黃金交叉，收盤 21201\\n────────────────────\\n💰 收盤: <b>21201</b>\\n📊 成交量: 202 口\\n📈 指標: MACD: 32.46  |  KD: K=69.4 D=84.8\\n🕐 時間: 09:38\",
        \"parse_mode\": \"HTML\"
    }")

if echo "$RESP2" | grep -q '"ok":true'; then
    echo "✅ 警示格式推播成功！"
else
    echo "❌ 警示格式推播失敗：$RESP2"
fi

echo ""
echo "4️⃣  用 Python notifier 測試..."
VENV_PYTHON="/Users/ckchiu/Desktop/Project/03-Data-Analytics/Stock_Analize/backend/capital_api/.venv/bin/python3"
BACKEND="/Users/ckchiu/Desktop/Project/03-Data-Analytics/Stock_Analize/backend"

$VENV_PYTHON -c "
import sys
sys.path.insert(0, '$BACKEND')
from capital_api.notifier import TelegramNotifier
n = TelegramNotifier(bot_token='$BOT_TOKEN', chat_id='$CHAT_ID')
result = n.send_message('✅ Python TelegramNotifier 推播測試成功！')
print('Python notifier:', '✅ 成功' if result else '❌ 失敗')

alert = {
    'name': 'KD 黃金交叉',
    'message': 'KD 黃金交叉，K=71.0 D=72.9',
    'level': 'high',
    'datetime': '09:38',
    'close': 21201,
    'volume': 202,
    'rsi': 63.0,
    'macd': 32.46,
    'k': 71.0,
    'd': 72.9,
}
result2 = n.send_alert(alert)
print('Python alert:', '✅ 成功' if result2 else '❌ 失敗')
"

echo ""
echo "========================================"
echo "✅ Telegram 推播驗證完成！"
echo "   請確認 Telegram 已收到 3~4 則訊息"
