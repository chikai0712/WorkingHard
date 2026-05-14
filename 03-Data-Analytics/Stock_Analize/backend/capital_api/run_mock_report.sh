#!/bin/bash
# ================================================================
# 台指期監控系統 — Mock 測試結果推播到 Telegram
# 必須在系統終端機（iTerm / Terminal.app）執行，不可在 Cursor terminal
# ================================================================

BOT_TOKEN="8771241397:AAESXT-Cn5EQ6sRBiHar1AKKwiQPKxJ_dJo"
CHAT_ID="229891358"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON="$BACKEND_DIR/venv/bin/python3"

# ── 清除所有 proxy（避免 Cursor sandbox 污染）──────────────
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
unset ALL_PROXY all_proxy SOCKS_PROXY SOCKS5_PROXY
unset socks_proxy socks5_proxy GIT_HTTP_PROXY GIT_HTTPS_PROXY

echo ""
echo "================================================================"
echo "  台指期監控系統 — Mock 測試結果推播"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================================"

# ── Step 0: 確認 Bot Token 有效 ────────────────────────────
echo ""
echo "[0/4] 驗證 Bot Token..."
BOT_INFO=$(curl -s --noproxy '*' --max-time 10 \
    "https://api.telegram.org/bot${BOT_TOKEN}/getMe")
if echo "$BOT_INFO" | grep -q '"ok":true'; then
    BOT_NAME=$(echo "$BOT_INFO" | python3 -c \
        "import sys,json; print(json.load(sys.stdin)['result']['username'])")
    echo "  ✅ Bot Token 有效 — @${BOT_NAME}"
else
    echo "  ❌ Bot Token 無效，中止"
    echo "  回應：$BOT_INFO"
    exit 1
fi

# ── Step 1: 執行 Python Mock，產生 JSON 結果 ───────────────
echo ""
echo "[1/4] 執行 Mock 資料產生..."

MOCK_JSON=$(MPLCONFIGDIR=/tmp/mpl_cache \
    TELEGRAM_BOT_TOKEN="$BOT_TOKEN" \
    TELEGRAM_CHAT_ID="$CHAT_ID" \
    "$PYTHON" -c "
import sys, os, json, math, random
from datetime import datetime, timedelta
sys.path.insert(0, '${BACKEND_DIR}')
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('ALL_PROXY', None)
os.environ.pop('all_proxy', None)

from capital_api.tick_processor import TickProcessor
from capital_api.alert_engine import AlertEngine

processor = TickProcessor()
base_price = 21000.0
base_time  = datetime(2026, 3, 25, 9, 0, 0)
bars = []

for minute in range(40):
    t = base_time + timedelta(minutes=minute)
    wave  = math.sin(minute * math.pi / 6) * 80
    trend = minute * 3
    for i in range(10):
        tt = t + timedelta(seconds=i*6)
        price = base_price + trend + wave + random.uniform(-8, 8)
        bar = processor.add_tick(price, random.randint(1,50), timestamp=tt)
        if bar: bars.append(bar)
processor.add_tick(base_price, 1, timestamp=base_time+timedelta(minutes=40))

ind = processor.get_indicators() or {}

engine = AlertEngine()
lc = bars[-1]['close'] if bars else base_price
engine.add_price_breakout(level=lc-30, direction='above', name='向上突破')
engine.add_price_breakout(level=lc+30, direction='below', name='向下跌破')
engine.add_custom(
    name='RSI > 40',
    condition=lambda b,i,p: (i or {}).get('rsi',0) > 40,
    message_fn=lambda b,i: f\"RSI={(i or {}).get('rsi',0):.1f}\",
)
alerts = []
if bars and ind:
    engine._prev_indicators = {
        'macd': (ind.get('macd') or 0)-5,
        'macd_signal': (ind.get('macd_signal') or 0)+5,
        'k': (ind.get('k') or 50)-5,
        'd': (ind.get('d') or 50)+5,
        'rsi': ind.get('rsi') or 50,
    }
    alerts = engine.check(bars[-1], ind)

result = {
    'bar_count': len(bars),
    'last_close': bars[-1]['close'] if bars else 0,
    'max_high': max(b['high'] for b in bars) if bars else 0,
    'min_low': min(b['low'] for b in bars) if bars else 0,
    'last3': [{'dt': b['datetime'][-5:], 'o': b['open'], 'h': b['high'],
               'l': b['low'], 'c': b['close'], 'v': b['volume']} for b in bars[-3:]],
    'rsi':    ind.get('rsi'),
    'macd':   ind.get('macd'),
    'macd_s': ind.get('macd_signal'),
    'macd_h': ind.get('macd_hist'),
    'k':      ind.get('k'),
    'd':      ind.get('d'),
    'bb_u':   ind.get('bb_upper'),
    'bb_m':   ind.get('bb_mid'),
    'bb_l':   ind.get('bb_lower'),
    'alerts': [{'name': a['name'], 'msg': a['message'], 'level': a['level']} for a in alerts],
}
print(json.dumps(result))
" 2>/dev/null)

if [ -z "$MOCK_JSON" ]; then
    echo "  ❌ Mock 資料產生失敗"
    exit 1
fi

BAR_COUNT=$(echo "$MOCK_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['bar_count'])")
ALERT_COUNT=$(echo "$MOCK_JSON" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['alerts']))")
echo "  ✅ ${BAR_COUNT} 根分鐘K，${ALERT_COUNT} 個警示觸發"

# ── Step 2: 產生趨勢線圖 ───────────────────────────────────
echo ""
echo "[2/4] 產生趨勢線圖..."

MPLCONFIGDIR=/tmp/mpl_cache "$PYTHON" -c "
import sys, os, math, random
from datetime import datetime, timedelta
sys.path.insert(0, '${BACKEND_DIR}')

from capital_api.tick_processor import TickProcessor
from capital_api.trendline_chart import plot_trendlines

processor = TickProcessor()
base_price = 21000.0
base_time  = datetime(2026, 3, 25, 9, 0, 0)

for minute in range(40):
    t = base_time + timedelta(minutes=minute)
    wave  = math.sin(minute * math.pi / 6) * 80
    trend = minute * 3
    for i in range(10):
        tt = t + timedelta(seconds=i*6)
        price = base_price + trend + wave + random.uniform(-8, 8)
        processor.add_tick(price, random.randint(1,50), timestamp=tt)
processor.add_tick(base_price, 1, timestamp=base_time+timedelta(minutes=40))

png = plot_trendlines(processor, title='TXF 1-Min K + Trendlines (Mock)', save_path='/tmp/mock_report_chart.png')
print(f'OK bytes: {len(png)}' if png else 'FAIL')
" 2>/dev/null

if [ -f /tmp/mock_report_chart.png ]; then
    SIZE=$(wc -c < /tmp/mock_report_chart.png | tr -d ' ')
    echo "  ✅ 圖表產生成功（${SIZE} bytes）→ /tmp/mock_report_chart.png"
    HAS_CHART=1
else
    echo "  ⚠️  圖表產生失敗，僅推播文字摘要"
    HAS_CHART=0
fi

# ── Step 3: 組裝摘要訊息並推播 ────────────────────────────
echo ""
echo "[3/4] 推播摘要訊息..."

SUMMARY=$(echo "$MOCK_JSON" | python3 -c "
import sys, json
from datetime import datetime
d = json.load(sys.stdin)

def f(v, dec=2):
    return f'{v:.{dec}f}' if v is not None else '—'

bars_text = '\\n'.join(
    f\"  {b['dt']}  O:{b['o']:.0f} H:{b['h']:.0f} L:{b['l']:.0f} C:{b['c']:.0f} V:{b['v']}\"
    for b in d['last3']
)
alert_text = '\\n'.join(
    f\"  {'🔴' if a['level']=='high' else '🟡' if a['level']=='medium' else '🟢'} {a['name']}: {a['msg']}\"
    for a in d['alerts']
) or '  (無警示觸發)'

print(f\"\"\"🧪 <b>台指期 Mock 測試報告</b>
🕐 $(date '+%Y-%m-%d %H:%M:%S')
────────────────────────
📊 <b>分鐘K 摘要</b>
  總根數: <b>{d['bar_count']}</b> 根
  最新收盤: <b>{d['last_close']:.0f}</b>
  最高: {d['max_high']:.0f}  最低: {d['min_low']:.0f}

<b>最近 3 根 K 棒</b>
<code>{bars_text}</code>
────────────────────────
📈 <b>技術指標</b>
  RSI: <b>{f(d['rsi'],1)}</b>
  MACD: {f(d['macd'])}  Signal: {f(d['macd_s'])}  Hist: {f(d['macd_h'])}
  KD  K: {f(d['k'],1)}  D: {f(d['d'],1)}
  BB  U:{f(d['bb_u'],0)} M:{f(d['bb_m'],0)} L:{f(d['bb_l'],0)}
────────────────────────
🔔 <b>警示觸發 ({len(d['alerts'])} 個)</b>
{alert_text}
────────────────────────
✅ <i>Mock 測試完成 — 非真實行情</i>\"\"\")
")

RESP=$(curl -s --noproxy '*' --max-time 10 \
    -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -H 'Content-Type: application/json' \
    -d "{\"chat_id\": \"${CHAT_ID}\", \"text\": $(echo "$SUMMARY" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))"), \"parse_mode\": \"HTML\"}")

if echo "$RESP" | grep -q '"ok":true'; then
    echo "  ✅ 摘要訊息推播成功"
else
    echo "  ❌ 摘要訊息推播失敗：$RESP"
fi

# ── Step 4: 推播趨勢線圖 ───────────────────────────────────
echo ""
echo "[4/4] 推播趨勢線圖..."

if [ "$HAS_CHART" -eq 1 ]; then
    LAST_CLOSE=$(echo "$MOCK_JSON" | python3 -c 