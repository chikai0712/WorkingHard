#!/usr/bin/env python3
"""
台指期監控系統 — Mock 測試腳本

不需要群益帳號、不需要 SKCOM、不需要 Windows。
在 Mac/Linux 上直接測試：
    - Tick 聚合成分鐘K
    - 技術指標計算（MACD / RSI / KD / 布林通道）
    - 警示引擎觸發
    - Telegram 推播（可選）

執行方式：
    cd backend/capital_api
    pip install pandas pandas-ta python-dotenv requests
    python test_mock.py

    # 若要測試 Telegram 推播：
    TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy python test_mock.py
"""

import os
import sys
import time
import random
import logging
from datetime import datetime, timedelta

# 加入 backend 目錄到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 設定 logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s — %(message)s',
)
logger = logging.getLogger('mock_test')


# ── 顏色輸出（terminal 用）──────────────────────────────────
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
def header(msg): print(f"\n{BOLD}{'='*60}\n  {msg}\n{'='*60}{RESET}")


# ══════════════════════════════════════════════════════════════
# TEST 1：模組匯入測試
# ══════════════════════════════════════════════════════════════
def test_imports():
    header("TEST 1：模組匯入")
    results = {}

    modules = [
        ('pandas',              'pandas'),
        ('pandas_ta',           'pandas-ta'),
        ('requests',            'requests'),
        ('tick_processor',      'capital_api.tick_processor'),
        ('alert_engine',        'capital_api.alert_engine'),
        ('notifier',            'capital_api.notifier')]

    for mod_name, display_name in modules:
        try:
            __import__(mod_name)
            ok(f"{display_name} 匯入成功")
            results[mod_name] = True
        except ImportError as e:
            err(f"{display_name} 匯入失敗：{e}")
            results[mod_name] = False

    return results


# ══════════════════════════════════════════════════════════════
# TEST 2：Tick 聚合 → 分鐘K
# ══════════════════════════════════════════════════════════════
def test_tick_aggregation():
    header("TEST 2：Tick 聚合 → 分鐘K")

    from capital_api.tick_processor import TickProcessor
    processor = TickProcessor()

    # 模擬 75 根分鐘K（需 ≥60 根才能讓 GEM RectangleDetector 正常偵測）
    # 每根 10 筆 Tick，需 ≥35 根才能算出 MACD Signal
    NUM_BARS = 75
    base_price = 21000.0
    base_time  = datetime(2026, 3, 24, 9, 0, 0)
    completed_bars = []

    import math
    for minute in range(NUM_BARS):
        t = base_time + timedelta(minutes=minute)
        # 每分鐘模擬 10 筆成交
        # 使用 sine wave 製造明顯波峰波谷（window=3 可識別）
        wave = math.sin(minute * math.pi / 6) * 80   # 週期 ~12 根
        trend = minute * 2                             # 緩慢上漲
        for tick_i in range(10):
            tick_time = t + timedelta(seconds=tick_i * 6)
            price_noise = random.uniform(-8, 8)
            price = base_price + trend + wave + price_noise
            vol   = random.randint(1, 50)

            bar = processor.add_tick(price, vol, timestamp=tick_time)
            if bar:
                completed_bars.append(bar)

    # 觸發最後一根（送入下一分鐘第一筆）
    last_tick_time = base_time + timedelta(minutes=NUM_BARS)
    processor.add_tick(base_price, 1, timestamp=last_tick_time)

    info(f"送入 Tick 數：{NUM_BARS * 10 + 1}")
    info(f"完成分鐘K數：{len(completed_bars)}")

    if len(completed_bars) >= 60:
        ok(f"分鐘K聚合正常（{len(completed_bars)} 根）")
    elif len(completed_bars) >= 35:
        warn(f"分鐘K聚合完成（{len(completed_bars)} 根），但不足 60 根，GEM 偵測將跳過")
    else:
        err(f"分鐘K數量不足（{len(completed_bars)}/35）")

    # 顯示最後 3 根
    print()
    print(f"  {'分鐘':20s}  {'開':>8s}  {'高':>8s}  {'低':>8s}  {'收':>8s}  {'量':>6s}")
    print(f"  {'-'*20}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*6}")
    for bar in completed_bars[-3:]:
        print(
            f"  {bar['datetime']:20s}  "
            f"{bar['open']:>8.0f}  {bar['high']:>8.0f}  "
            f"{bar['low']:>8.0f}  {bar['close']:>8.0f}  {bar['volume']:>6d}"
        )

    return processor, completed_bars


# ══════════════════════════════════════════════════════════════
# TEST 3：技術指標計算
# ══════════════════════════════════════════════════════════════
def test_indicators(processor):
    header("TEST 3：技術指標計算")

    indicators = processor.get_indicators()

    if indicators is None:
        err("指標計算失敗（K棒數量不足或 pandas-ta 未安裝）")
        return None

    ok(f"指標計算成功（基於 {indicators.get('bar_count', '?')} 根分鐘K）")

    indicator_map = [
        ('macd',       'MACD 線'),
        ('macd_signal','MACD Signal'),
        ('macd_hist',  'MACD Histogram'),
        ('rsi',        'RSI'),
        ('k',          'KD — K'),
        ('d',          'KD — D'),
        ('bb_upper',   '布林上軌'),
        ('bb_mid',     '布林中軌'),
        ('bb_lower',   '布林下軌'),
        ('close',      '最新收盤')]

    print()
    for key, label in indicator_map:
        val = indicators.get(key)
        if val is not None:
            ok(f"{label:15s}: {val:.2f}")
        else:
            warn(f"{label:15s}: 無法計算（K棒不足）")

    return indicators


# ══════════════════════════════════════════════════════════════
# TEST 4：警示引擎觸發
# ══════════════════════════════════════════════════════════════
def test_alert_engine(completed_bars, indicators):
    header("TEST 4：警示引擎觸發")

    if not completed_bars or indicators is None:
        warn("跳過（無分鐘K或指標資料）")
        return []

    from capital_api.alert_engine import AlertEngine
    engine = AlertEngine()

    # 額外加入價格突破規則（用實際最新收盤價 ± 50 模擬）
    last_close = completed_bars[-1]['close']
    engine.add_price_breakout(level=last_close - 30, direction='above', name='測試：向上突破')
    engine.add_price_breakout(level=last_close + 30, direction='below', name='測試：向下跌破')

    # 加入自訂條件
    engine.add_custom(
        name='自訂條件：RSI > 40',
        condition=lambda bar, ind, prev: ind.get('rsi', 0) > 40,
        message_fn=lambda bar, ind: f"RSI = {ind.get('rsi', 0):.1f}",
    )

    # 用最後一根 K 棒 + 最新指標做一次完整檢查
    last_bar = completed_bars[-1]
    info(f"檢查分鐘K：{last_bar['datetime']}  收:{last_bar['close']:.0f}  量:{last_bar['volume']}")

    # 模擬前一根指標（製造交叉條件）
    engine._prev_indicators = {
        'macd':       indicators.get('macd', 0) - 5,
        'macd_signal':indicators.get('macd_signal', 0) + 5,
        'k':          indicators.get('k', 50) - 5,
        'd':          indicators.get('d', 50) + 5,
        'rsi':        indicators.get('rsi', 50)}

    alerts = engine.check(last_bar, indicators)

    print()
    if alerts:
        ok(f"觸發 {len(alerts)} 個警示：")
        for alert in alerts:
            level_color = GREEN if alert['level'] == 'high' else YELLOW
            print(f"   {level_color}[{alert['level'].upper()}]{RESET} {alert['name']}: {alert['message']}")
    else:
        info("本次無警示觸發（條件未滿足）")

    return alerts


# ══════════════════════════════════════════════════════════════
# TEST 4b：趨勢線計算 + 圖表產生
# ══════════════════════════════════════════════════════════════
def test_trendlines(processor, completed_bars):
    header("TEST 4b：趨勢線計算 + 圖表產生")

    if len(completed_bars) < 15:
        warn("K 棒數量不足（< 15），跳過趨勢線測試")
        return

    # 計算趨勢線
    tl = processor.get_trendlines(window=3)

    info(f"掃描 {tl['bar_count']} 根分鐘K")
    info(f"Swing High 數量：{len(tl['swing_highs'])}")
    info(f"Swing Low  數量：{len(tl['swing_lows'])}")
    print()

    if tl['support']:
        s = tl['support']
        ok(f"上升支撐線：現值 {s['value']:.1f}，斜率 {s['slope']:+.2f}/根")
    else:
        warn("上升支撐線：Swing Low 不足，無法計算")

    if tl['resistance']:
        r = tl['resistance']
        ok(f"下降壓力線：現值 {r['value']:.1f}，斜率 {r['slope']:+.2f}/根")
    else:
        warn("下降壓力線：Swing High 不足，無法計算")

    # 產生圖表
    print()
    info("產生趨勢線圖表...")
    try:
        from capital_api.trendline_chart import plot_trendlines
        chart_path = '/tmp/trendline_test.png'
        png_bytes = plot_trendlines(
            processor,
            title='TXF 1-Min K + Trendlines (Mock Test)',
            save_path=chart_path,
        )
        if png_bytes:
            ok(f"圖表產生成功（{len(png_bytes):,} bytes）→ {chart_path}")
        else:
            err("圖表產生失敗")
    except ImportError as e:
        warn(f"matplotlib 未安裝，跳過圖表：{e}")
    except Exception as e:
        err(f"圖表產生錯誤：{e}")


# ══════════════════════════════════════════════════════════════
# TEST 4c：GEM 框型價位計算
# ══════════════════════════════════════════════════════════════
def test_gem_price_target(processor, completed_bars):
    header("TEST 4c：GEM 框型價位計算")

    if len(completed_bars) < 15:
        warn("K 棒數量不足（< 15），跳過 GEM 測試")
        return

    # 方法 1：透過 get_indicators() 自動取得（最常用）
    indicators = processor.get_indicators()
    gem = indicators.get('gem') if indicators else None

    info("方法 1：透過 get_indicators()['gem'] 取得")
    if gem is None:
        warn("GEM 偵測結果為 None（K棒不足或 price_target 未安裝）")
    else:
        status_color = GREEN if 'breakout' in gem['status'] else BLUE
        print(f"  狀態：{status_color}{gem['status']}{RESET}")
        print(f"  阻力位：{gem['resistance']:.0f}")
        print(f"  支撐位：{gem['support']:.0f}")
        print(f"  區間大小：{gem['height']:.0f} 點")
        print(f"  框型中線：{gem['mid']:.0f}")

        if gem.get('tp1') is not None:
            direction_txt = '向上突破 📈' if gem['direction'] == 'up' else '向下跌破 📉'
            print()
            ok(f"突破方向：{direction_txt}")
            ok(f"突破確認價：{gem['breakout_price']:.0f}")
            ok(f"起漲/起跌：{gem['origin_price']:.0f}")
            ok(f"TP1（框型一倍）：{gem['tp1']:.0f}")
            ok(f"TP2（翻亞當）：  {gem['tp2']:.0f}")
            ok(f"SL（初始停損）：  {gem['sl']:.0f}")
        else:
            info("目前在區間內（無突破），僅顯示區間資訊")

    # 方法 2：直接呼叫 processor._gem_detector
    print()
    info("方法 2：直接呼叫 RectangleDetector（手動指定阻力/支撐）")
    try:
        from capital_api.price_target import (
            calc_rectangle, calc_adam, calc_full_plan, format_plan_message
        )

        # 用 completed_bars 的最高/最低模擬一個突破場景
        bars_closes = [b['close'] for b in completed_bars]
        bars_highs  = [b['high']  for b in completed_bars]
        bars_lows   = [b['low']   for b in completed_bars]
        resistance  = max(bars_highs[-30:]) if len(bars_highs) >= 30 else max(bars_highs)
        support     = min(bars_lows[-30:])  if len(bars_lows)  >= 30 else min(bars_lows)
        last_close  = bars_closes[-1]

        ok(f"區間：{support:.0f} ~ {resistance:.0f}（高度 {resistance-support:.0f} 點）")

        # 框型計算
        rect = calc_rectangle(resistance, support)
        ok(f"框型 TP（向上）：{rect['tp_up']:.0f}  框型 TP（向下）：{rect['tp_down']:.0f}")

        # 翻亞當（假設從支撐突破向上）
        origin     = support + (resistance - support) * 0.1   # 起漲點（略高於支撐）
        adam_price = resistance + 1  # 模擬剛突破阻力
        adam = calc_adam(breakout_price=adam_price, origin_price=origin)
        ok(f"翻亞當目標（向上）：{adam['target']:.0f}（距突破點 {adam['distance']:.0f} 點）")

        # 完整計畫
        plan = calc_full_plan(
            resistance=resistance,
            support=support,
            breakout_price=adam_price,
            origin_price=origin,
            sl_offset=20.0,
        )
        print()
        info("完整 GEM 交易計畫：")
        print(format_plan_message(plan))

    except ImportError as e:
        warn(f"price_target 未安裝：{e}")
    except Exception as e:
        err(f"GEM 直接呼叫發生例外：{e}")


# ══════════════════════════════════════════════════════════════
# TEST 5：Telegram 推播
# ══════════════════════════════════════════════════════════════
def test_telegram(alerts, processor=None):
    header("TEST 5：Telegram 推播")

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    chat_id   = os.getenv('TELEGRAM_CHAT_ID', '')

    if not bot_token or not chat_id:
        warn("未設定 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID，跳過推播測試")
        info("設定方式：TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy python test_mock.py")
        return

    try:
        from capital_api.notifier import TelegramNotifier
        notifier = TelegramNotifier(bot_token=bot_token, chat_id=chat_id)

        # 測試基本訊息
        result = notifier.send_message("🧪 台指期監控系統 Mock 測試訊息")
        if result:
            ok("Telegram 基本訊息推播成功")
        else:
            err("Telegram 基本訊息推播失敗")

        # 推播警示
        for alert in alerts[:2]:  # 最多推播 2 個
            notifier.send_alert(alert)
            ok(f"警示推播：{alert['name']}")
            time.sleep(0.5)

        # 推播趨勢線圖（若有 processor）
        if processor is not None:
            info("測試趨勢線圖推播...")
            result = notifier.send_trendline_chart(
                processor,
                caption="🧪 <b>Mock 測試</b> — 趨勢線圖",
            )
            if result:
                ok("趨勢線圖推播成功")
            else:
                err("趨勢線圖推播失敗（可能是 K 棒數量不足或 matplotlib 未安裝）")

    except Exception as e:
        err(f"Telegram 測試發生例外：{e}")


# ══════════════════════════════════════════════════════════════
# TEST 6：即時模擬（可選，按 Ctrl+C 停止）
# ══════════════════════════════════════════════════════════════
def test_realtime_simulation():
    header("TEST 6：即時模擬（Ctrl+C 停止）")
    info("模擬台指期即時報價（每 0.5 秒一筆 Tick）...")
    print()

    from capital_api.tick_processor import TickProcessor
    from capital_api.alert_engine   import AlertEngine

    processor = TickProcessor()
    engine    = AlertEngine()
    engine.add_price_breakout(level=21050, direction='above')
    engine.add_price_breakout(level=20950, direction='below')

    price = 21000.0
    tick_count = 0

    try:
        while True:
            # 隨機遊走模擬價格
            price += random.gauss(0, 8)
            price  = max(20800, min(21200, price))
            vol    = random.randint(1, 100)

            bar = processor.add_tick(price, vol)
            tick_count += 1

            print(f"\r  Tick #{tick_count:4d}  價格: {price:8.0f}  量: {vol:3d}  ", end='', flush=True)

            if bar:
                indicators = processor.get_indicators()
                print()
                info(
                    f"分鐘K完成 [{bar['datetime']}] "
                    f"O:{bar['open']:.0f} H:{bar['high']:.0f} "
                    f"L:{bar['low']:.0f} C:{bar['close']:.0f} V:{bar['volume']}"
                )

                if indicators:
                    rsi  = indicators.get('rsi', '—')
                    macd = indicators.get('macd', '—')
                    k    = indicators.get('k', '—')
                    d    = indicators.get('d', '—')
                    rsi_str  = f"{rsi:.1f}"  if isinstance(rsi,  float) else str(rsi)
                    macd_str = f"{macd:.2f}" if isinstance(macd, float) else str(macd)
                    k_str    = f"{k:.1f}"    if isinstance(k,    float) else str(k)
                    d_str    = f"{d:.1f}"    if isinstance(d,    float) else str(d)
                    info(f"  指標 RSI:{rsi_str}  MACD:{macd_str}  K:{k_str} D:{d_str}")

                    alerts = engine.check(bar, indicators)
                    for alert in alerts:
                        print(f"  {RED}{BOLD}🔔 警示：{alert['name']} — {alert['message']}{RESET}")

            time.sleep(0.5)

    except KeyboardInterrupt:
        stats = processor.get_stats()
        print()
        ok(f"即時模擬結束 — 共 {tick_count} 筆 Tick，{stats['bar_count']} 根分鐘K")


# ══════════════════════════════════════════════════════════════
# 主程式
# ══════════════════════════════════════════════════════════════
def main():
    print(f"")
    print(f"{BOLD}台指期監控系統 — Mock 測試{RESET}")
    print(f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # TEST 1：匯入
    import_results = test_imports()

    # TEST 2：Tick 聚合
    processor, completed_bars = test_tick_aggregation()

    # TEST 3：技術指標
    indicators = test_indicators(processor)

    # TEST 4：警示引擎
    alerts = test_alert_engine(completed_bars, indicators)

    # TEST 4b：趨勢線計算 + 圖表產生
    test_trendlines(processor, completed_bars)

    # TEST 4c：GEM 框型價位計算
    test_gem_price_target(processor, completed_bars)

    # TEST 5：Telegram（需設定環境變數）
    test_telegram(alerts, processor)

    # 摘要
    header("測試摘要")
    ok(f"Tick 聚合：{len(completed_bars)} 根分鐘K")
    ok(f"技術指標：{'正常' if indicators else '失敗'}")
    ok(f"警示引擎：觸發 {len(alerts)} 個警示")
    ok("GEM 框型：已整合至 get_indicators()['gem']")
    print()

    # TEST 6：即時模擬（互動模式，--ci 旗標跳過）
    ci_mode = '--ci' in sys.argv or os.getenv('CI', '') != ''
    if ci_mode:
        info("CI 模式：跳過 TEST 6 即時模擬")
    else:
        info("TEST 6：即時模擬？（輸入 y 開始，其他鍵跳過）")
        try:
            ans = input("  > ").strip().lower()
            if ans == 'y':
                test_realtime_simulation()
        except (EOFError, KeyboardInterrupt):
            pass

    print(f"\n{BOLD}全部測試完成。{RESET}\n")


if __name__ == '__main__':
    main()
