#!/bin/bash
# ══════════════════════════════════════════════════════════════════
# A-06b: Telegram Token 實測腳本
# 在系統終端機（iTerm / Terminal.app）執行，繞過 Cursor sandbox
#
# 執行方式：
#   cd /Users/ckchiu/Desktop/Project/03-Data-Analytics/Stock_Analize/backend/capital_api
#   bash run_a06b.sh
# ══════════════════════════════════════════════════════════════════

set -e

BOT_TOKEN="8771241397:AAESXT-Cn5EQ6sRBiHar1AKKwiQPKxJ_dJo"
CHAT_ID="229891358"
VENV_PYTHON="$(cd "$(dirname "$0")" && pwd)/.venv/bin/python3"
BACKEND="$(cd "$(dirname "$0")/../.." && pwd)/backend"
CAPITAL_API_DIR="$(cd "$(dirname "$0")" && pwd)"

# 顏色
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[0;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'
ok()   { echo -e "${GREEN}  ✅ $*${RESET}"; }
fail() { echo -e "${RED}  ❌ $*${RESET}"; }
warn() { echo -e "${YELLOW}  ⚠️  $*${RESET}"; }
info() { echo -e "${BLUE}  ℹ️  $*${RESET}"; }

echo -e "\n${BOLD}╔══════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║  台指期監控系統 — A-06b Telegram 實測        ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════════╝${RESET}"
echo -e "  時間：$(date '+%Y-%m-%d %H:%M:%S')"
echo -e "  Python：$VENV_PYTHON"

# ── 清除 proxy（繞過 Cursor sandbox）──────────────────────────
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
unset ALL_PROXY all_proxy SOCKS_PROXY SOCKS5_PROXY socks_proxy socks5_proxy

PASS=0; FAIL=0

# ══════════════════════════════════════════════════════════════════
# TEST 1: curl 確認網路可連到 Telegram
# ══════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}[TEST 1] curl 網路連線測試...${RESET}"
BOT_INFO=$(curl -s --max-time 10 "https://api.telegram.org/bot${BOT_TOKEN}/getMe" 2>&1)
if echo "$BOT_INFO" | grep -q '"ok":true'; then
    BOT_NAME=$(echo "$BOT_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['username'])" 2>/dev/null || echo '?')
    ok "Bot Token 有效 — @${BOT_NAME}"; ((PASS++))
else
    fail "Bot Token 無效或無法連線：$BOT_INFO"; ((FAIL++))
    echo -e "${RED}  ⛔ 網路不通，請確認在 iTerm 執行（非 Cursor terminal）${RESET}"
    exit 1
fi

# ══════════════════════════════════════════════════════════════════
# TEST 2: 發送基本文字訊息
# ══════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}[TEST 2] 基本文字訊息推播...${RESET}"
RESP=$(curl -s --max-time 10 -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -H 'Content-Type: application/json' \
    -d "{
        \"chat_id\": \"${CHAT_ID}\",
        \"text\": \"🧪 <b>A-06b 測試 [1/4]</b>\\n\\n基本推播驗證\\n時間：$(date '+%Y-%m-%d %H:%M:%S')\",
        \"parse_mode\": \"HTML\"
    }")
if echo "$RESP" | grep -q '"ok":true'; then
    ok "基本訊息推播成功"; ((PASS++))
else
    fail "推播失敗：$RESP"; ((FAIL++))
fi

# ══════════════════════════════════════════════════════════════════
# TEST 3: 發送警示格式訊息
# ══════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}[TEST 3] 警示格式推播...${RESET}"
RESP2=$(curl -s --max-time 10 -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -H 'Content-Type: application/json' \
    -d "{
        \"chat_id\": \"${CHAT_ID}\",
        \"text\": \"🔴 <b>台指期警示 [A-06b TEST 2/4]</b>\\n────────────────────\\n📌 <b>MACD 黃金交叉</b>\\n📝 MACD 黃金交叉，收盤 21201\\n────────────────────\\n💰 收盤: <b>21201</b>\\n📊 成交量: 202 口\\n📈 指標: MACD: 32.46  |  KD: K=69.4 D=84.8\\n🕐 時間: 09:38\",
        \"parse_mode\": \"HTML\"
    }")
if echo "$RESP2" | grep -q '"ok":true'; then
    ok "警示格式推播成功"; ((PASS++))
else
    fail "警示格式推播失敗：$RESP2"; ((FAIL++))
fi

# ══════════════════════════════════════════════════════════════════
# TEST 4: Python TelegramNotifier.send_message / send_alert
# ══════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}[TEST 4] Python TelegramNotifier 推播...${RESET}"
if [ ! -f "$VENV_PYTHON" ]; then
    warn ".venv 不存在：$VENV_PYTHON"
    ((FAIL++))
else
    RESULT=$( MPLCONFIGDIR=/tmp/mpl_cache "$VENV_PYTHON" -c "
import sys, os
sys.path.insert(0, '$(dirname "$CAPITAL_API_DIR")')
from capital_api.notifier import TelegramNotifier
n = TelegramNotifier(bot_token='$BOT_TOKEN', chat_id='$CHAT_ID')

r1 = n.send_message('<b>✅ Python TelegramNotifier [A-06b TEST 3/4]</b>\nsend_message() 正常運作', parse_mode='HTML')
print('send_message:', 'OK' if r1 else 'FAIL')

alert = {
    'name': 'KD 黃金交叉',
    'message': 'KD 黃金交叉，K=71.0 D=72.9 [A-06b TEST 4/4]',
    'level': 'high',
    'datetime': '09:38',
    'close': 21201,
    'volume': 202,
    'rsi': 63.0,
    'macd': 32.46,
    'k': 71.0,
    'd': 72.9,
}
r2 = n.send_alert(alert)
print('send_alert:', 'OK' if r2 else 'FAIL')
" 2>&1 )

    echo "$RESULT" | while IFS= read -r line; do
        if echo "$line" | grep -q ': OK'; then
            ok "$line"; 
        elif echo "$line" | grep -q ': FAIL'; then
            fail "$line"
        else
            info "$line"
        fi
    done

    if echo "$RESULT" | grep -q 'FAIL'; then
        ((FAIL++))
    else
        ((PASS+=2))
    fi
fi

# ══════════════════════════════════════════════════════════════════
# TEST 5: send_mock_report.py 完整流程（含趨勢線圖）
# ══════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}[TEST 5] send_mock_report.py 完整流程（含趨勢線圖）...${RESET}"
if [ ! -f "$VENV_PYTHON" ]; then
    warn ".venv 不存在，跳過"; ((FAIL++))
else
    MOCK_OUT=$( cd "$CAPITAL_API_DIR" && \
        MPLCONFIGDIR=/tmp/mpl_cache \
        TELEGRAM_BOT_TOKEN="$BOT_TOKEN" \
        TELEGRAM_CHAT_ID="$CHAT_ID" \
        "$VENV_PYTHON" send_mock_report.py 2>&1 )

    echo "$MOCK_OUT" | while IFS= read -r line; do
        if echo "$line" | grep -q '✅'; then
            ok "$line"
        elif echo "$line" | grep -q '❌'; then
            fail "$line"
        elif echo "$line" | grep -q '⚠️'; then
            warn "$line"
        else
            info "$line"
        fi
    done

    if echo "$MOCK_OUT" | grep -q '❌'; then
        ((FAIL++))
    else
        ((PASS++))
    fi
fi

# ══════════════════════════════════════════════════════════════════
# 總結
# ══════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}╔══════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║  測試結果總結                                ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════════╝${RESET}"
echo -e "  通過：${GREEN}${PASS}${RESET}  失敗：${RED}${FAIL}${RESET}"

if [ "$FAIL" -eq 0 ]; then
    echo -e "\n${GREEN}${BOLD}  ✅ A-06b 全部通過！Telegram 推播驗證完成。${RESET}"
    echo -e "${GREEN}  請確認 Telegram 已收到 6~8 則訊息（含趨勢線圖）。${RESET}"
    echo -e "\n${BOLD}  下一步：A-07 Windows 部署${RESET}"
else
    echo -e "\n${RED}${BOLD}  ❌ 有 ${FAIL} 個測試失敗，請檢查上方錯誤訊息。${RESET}"
    exit 1
fi
