#!/usr/bin/env python3
"""
台指期監控系統 — Mock 測試結果推播到 Telegram

執行方式：
    cd backend/capital_api
    MPLCONFIGDIR=/tmp/mpl_cache \
    TELEGRAM_BOT_TOKEN=8771241397:AAESXT-Cn5EQ6sRBiHar1AKKwiQPKxJ_dJo \
    TELEGRAM_CHAT_ID=229891358 \
    .venv/bin/python3 send_mock_report.py

    # 或直接用 run_a06b.sh（含全部測試）：
    bash run_a06b.sh
"""

import os
import sys
import math
import random
import logging
from datetime import datetime, timedelta

# ── path setup ──────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.WARNING)  # 只顯示 WARNING+，讓輸出乾淨
logger = logging.getLogger('send_mock_report')

GREEN  = '\033[92m'
YELLOW = '\033[93m'
RED    = '\033[91m'
BLUE   = '\033[94m'
RESET  = '\033[0m'
BOLD   = '\033[1m'

def ok(msg):   print(f"{GREEN}  ✅ {msg}{RESET}")
def warn(msg): print(f"{YELLOW}  ⚠️  {msg}{RESET}")
def err(msg):  print(f"{RED}  ❌ {msg}{RESET}")
def info(msg): print(f"{BLUE}  ℹ️  {msg}{RESET}")


# ════════════════════════════════════════════════════════════
# Step 1：產生 Mock 資料（Tick → 分鐘K → 指標 → 警示）
# ════════════════════════════════════════════════════════════
def run_mock() -> dict:
    print(f"\n{BOLD}[1/4] 產生 Mock 資料...{RESET}")

    from capital_api.tick_processor import TickProcessor
    from capital_api.alert_engine import AlertEngine

    processor = TickProcessor()
    base_price = 21000.0
    base_time  = datetime(2026, 3, 25, 9, 0, 0)
    completed_bars = []

    # 模擬 40 根分鐘K（sine wave + trend）
    for minute in range(40):
        t = base_time + timedelta(minutes=minute)
        wave  = math.sin(minute * math.pi / 6) * 80
        trend = minute * 3
        for tick_i in range(10):
            tick_time = t + timedelta(seconds=tick_i * 6)
            price = base_price + trend + wave + random.uniform(-8, 8)
            bar = processor.add_tick(price, random.randint(1, 50), timestamp=tick_time)
            if bar:
                completed_bars.append(bar)

    # flush 最後一根
    processor.add_tick(base_price, 1, timestamp=base_time + timedelta(minutes=40))

    indicators = processor.get_indicators()

    # 警示引擎
    engine = AlertEngine()
    last_close = completed_bars[-1]['close'] if completed_bars else base_price
    engine.add_price_breakout(level=last_close - 30, direction='above', name='向上突破')
    engine.add_price_breakout(level=last_close + 30, direction='below', name='向下跌破')
    engine.add_custom(
        name='RSI > 40',
        condition=lambda bar, ind, prev: (ind or {}).get('rsi', 0) > 40,
        message_fn=lambda bar, ind: f"RSI = {(ind or {}).get('rsi', 0):.1f}",
    )

    alerts = []
    if completed_bars and indicators:
        engine._prev_indicators = {
            'macd':        (indicators.get('macd') or 0) - 5,
            'macd_signal': (indicators.get('macd_signal') or 0) + 5,
            'k':           (indicators.get('k') or 50) - 5,
            'd':           (indicators.get('d') or 50) + 5,
            'rsi':         indicators.get('rsi') or 50,
        }
        alerts = engine.check(completed_bars[-1], indicators)

    ok(f"{len(completed_bars)} 根分鐘K，{len(alerts)} 個警示觸發")

    return {
        'processor':     processor,
        'completed_bars': completed_bars,
        'indicators':    indicators,
        'alerts':        alerts,
        'last_close':    last_close,
    }


# ════════════════════════════════════════════════════════════
# Step 2：產生趨勢線圖（PNG bytes）
# ════════════════════════════════════════════════════════════
def make_chart(processor) -> bytes | None:
    print(f"\n{BOLD}[2/4] 產生趨勢線圖...{RESET}")
    try:
        from capital_api.trendline_chart import plot_trendlines
        png_bytes = plot_trendlines(
            processor,
            title='TXF 1-Min K + Trendlines (Mock Report)',
            save_path='/tmp/mock_report_chart.png',
        )
        if png_bytes:
            ok(f"圖表 {len(png_bytes):} bytes → /tmp/mock_report_chart.png")
            return png_bytes
        else:
            warn("圖表產生失敗（K 棒不足或 matplotlib 未安裝）")
            return None
    except Exception as e:
        warn(f"圖表例外：{e}")
        return None


# ════════════════════════════════════════════════════════════
# Step 3：組裝摘要訊息
# ════════════════════════════════════════════════════════════
def build_summary_text(data: dict) -> str:
    indicators   = data['indicators'] or {}
    bars         = data['completed_bars']
    alerts       = data['alerts']
    last_close   = data['last_close']
    last_bar     = bars[-1] if bars else {}
    now_str      = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # ── 指標欄位 ──────────────────────────────────────────
    def _fmt(v, dec=2):
        return f"{v:.{dec}f}" if v is not None else '—'

    macd_line = (
        f"MACD: {_fmt(indicators.get('macd'))}  "
        f"Signal: {_fmt(indicators.get('macd_signal'))}  "
        f"Hist: {_fmt(indicators.get('macd_hist'))}"
    )
    kd_line = (
        f"K: {_fmt(indicators.get('k'), 1)}  "
        f"D: {_fmt(indicators.get('d'), 1)}"
    )
    bb_line = (
        f"Upper: {_fmt(indicators.get('bb_upper'), 0)}  "
        f"Mid: {_fmt(indicators.get('bb_mid'), 0)}  "
        f"Lower: {_fmt(indicators.get('bb_lower'), 0)}"
    )

    # ── 最後 3 根 K 棒 ────────────────────────────────────
    bar_lines = []
    for b in bars[-3:]:
        bar_lines.append(
            f"  {b['datetime'][-5:]}  "
            f"O:{b['open']:.0f} H:{b['high']:.0f} "
            f"L:{b['low']:.0f} C:{b['close']:.0f} V:{b['volume']}"
        )
    bars_text = '\n'.join(bar_lines) or '  (無資料)'

    # ── 警示清單 ──────────────────────────────────────────
    alert_lines = []
    for a in alerts:
        emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(a.get('level', 'medium'), '⚪')
        alert_lines.append(f"  {emoji} {a['name']}: {a['message']}")
    alerts_text = '\n'.join(alert_lines) or '  (無警示觸發)'

    text = (
        f"🧪 <b>台指期 Mock 測試報告</b>\n"
        f"🕐 {now_str}\n"
        f"{'─'*24}\n"
        f"📊 <b>分鐘K 摘要</b>\n"
        f"  總根數: {len(bars)} 根\n"
        f"  最新收盤: <b>{last_close:.0f}</b>\n"
        f"  最高: {max(b['high'] for b in bars):.0f}  "
        f"最低: {min(b['low'] for b in bars):.0f}\n"
        f"\n"
        f"<b>最近 3 根 K 棒</b>\n"
        f"<code>{bars_text}</code>\n"
        f"{'─'*24}\n"
        f"📈 <b>技術指標</b>\n"
        f"  RSI: <b>{_fmt(indicators.get('rsi'), 1)}</b>\n"
        f"  {macd_line}\n"
        f"  KD  {kd_line}\n"
        f"  BB  {bb_line}\n"
        f"{'─'*24}\n"
        f"🔔 <b>警示觸發 ({len(alerts)} 個)</b>\n"
        f"{alerts_text}\n"
        f"{'─'*24}\n"
        f"✅ <i>Mock 測試完成 — 非真實行情</i>"
    )
    return text


# ════════════════════════════════════════════════════════════
# Step 4：推播到 Telegram
# ════════════════════════════════════════════════════════════
def send_to_telegram(summary_text: str, png_bytes: bytes | None, data: dict):
    print(f"\n{BOLD}[3/4] 發送到 Telegram...{RESET}")

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
    chat_id   = os.getenv('TELEGRAM_CHAT_ID',   '').strip()

    if not bot_token or not chat_id:
        # fallback：使用已驗證的 hardcoded token（僅供開發測試）
        bot_token = '8771241397:AAESXT-Cn5EQ6sRBiHar1AKKwiQPKxJ_dJo'
        chat_id   = '229891358'
        warn("未設定環境變數，使用預設 Token（開發測試用）")

    from capital_api.notifier import TelegramNotifier
    n = TelegramNotifier(bot_token=bot_token, chat_id=chat_id)

    # 1. 傳送文字摘要
    r1 = n.send_message(summary_text)
    if r1:
        ok("摘要訊息推播成功")
    else:
        err("摘要訊息推播失敗")

    # 2. 傳送趨勢線圖（若有）
    if png_bytes:
        indicators = data['indicators'] or {}
        processor  = data['processor']
        tl         = processor.get_trendlines()
        sup = f"{tl['support']['value']:.0f}"    if tl.get('support')    else '-'
        res = f"{tl['resistance']['value']:.0f}" if tl.get('resistance') else '-'
        direction = (
            'Uptrend'   if tl.get('support')    and tl['support']['slope']    >  0.5 else
            'Downtrend' if tl.get('resistance') and tl['resistance']['slope'] < -0.5 else
            'Sideways'
        )
        caption = (
            f"📉 TXF Mock Trendline Chart\n"
            f"Trend: {direction}\n"
            f"Support: {sup}  Resistance: {res}\n"
            f"RSI: {(indicators.get('rsi') or 0):.1f}  "
            f"MACD: {(indicators.get('macd') or 0):.2f}"
        )
        r2 = n.send_photo(png_bytes, caption=caption)
        if r2:
            ok("趨勢線圖推播成功")
        else:
            err("趨勢線圖推播失敗")

    # 3. 傳送每個高等級警示（含完整 OHLCV + 技術指標）
    print(f"\n{BOLD}[4/4] 推播個別警示 + GEM 計畫...{RESET}")
    bars = data['completed_bars']
    last = bars[-1] if bars else {}
    indicators = data['indicators'] or {}
    gem = indicators.get('gem')

    high_alerts = [a for a in data['alerts'] if a.get('level') == 'high']
    if high_alerts:
        for a in high_alerts:
            r3 = n.send_alert(
                alert=a,
                bar=last,
                indicators=indicators,
                gem=gem,
            )
            if r3:
                ok(f"警示推播：{a['name']}")
            else:
                err(f"警示推播失敗：{a['name']}")
    else:
        info("無高等級警示需單獨推播")

    # 4. GEM 框型突破計畫（Mock 固定數值）
    from capital_api.price_target import calc_full_plan
    mock_plan = calc_full_plan(
        resistance=21300,
        support=21000,
        breakout_price=21320,
        origin_price=21050,
        sl_offset=20,
    )
    r4 = n.send_gem_plan(mock_plan)
    if r4:
        ok("GEM 框型突破計畫推播成功")
    else:
        err("GEM 框型突破計畫推播失敗")


# ════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════
def main():
    print(f"\n{BOLD}台指期監控系統 — Mock 測試結果推播{RESET}")
    print(f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: 產生 Mock 資料
    data = run_mock()

    # Step 2: 產生趨勢線圖
    png_bytes = make_chart(data['processor'])

    # Step 3 & 4: 組裝摘要 + 推播
    summary_text = build_summary_text(data)
    send_to_telegram(summary_text, png_bytes, data)

    print(f"\n{BOLD}完成！請查看 Telegram。{RESET}\n")


if __name__ == '__main__':
    main() 