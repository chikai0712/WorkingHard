"""
台指期當沖監控系統 — Windows 主程式

功能：
- 連線群益 Capital API，訂閱台指期近月 Tick
- 每分鐘聚合 Tick 成分鐘K
- 計算技術指標（MACD / RSI / KD / 布林通道）
- 條件觸發時發送 Telegram 警示

執行方式（Windows 電腦）：
    python windows_monitor.py

前置條件：
    1. 已安裝 SKCOM：執行 CapitalAPI_2/元件/x64/install.bat
    2. 已設定 .env 檔案（複製 .env.example）
    3. pip install -r requirements.txt
"""

import os
import sys
import time
import signal
import logging
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# 設定 logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s — %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('monitor.log', encoding='utf-8'),
    ]
)
logger = logging.getLogger('windows_monitor')

# 加入 backend 目錄到 Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from capital_api.client import CapitalClient
from capital_api.futures_subscriber import FuturesSubscriber
from capital_api.tick_processor import TickProcessor
from capital_api.alert_engine import AlertEngine
from capital_api.notifier import TelegramNotifier


# ── 全域停止旗標 ───────────────────────────────────────────
_running = True

# 趨勢線圖定時推播：每 N 分鐘推一次（0 = 停用）
CHART_INTERVAL_MINUTES: int = int(os.getenv('CHART_INTERVAL_MINUTES', '30'))
_last_chart_minute: Optional[str] = None   # 記錄上次推圖的分鐘 key

# GEM 框型偵測：每 N 分鐘最多觸發一次（避免同區間重複推播）
GEM_COOLDOWN_MINUTES: int = int(os.getenv('GEM_COOLDOWN_MINUTES', '15'))
_last_gem_minute: Optional[str] = None     # 記錄上次 GEM 推播的分鐘 key
_last_gem_status: Optional[str] = None    # 上次偵測狀態（避免同狀態重複推）

def _signal_handler(sig, frame):
    global _running
    logger.info("收到停止訊號，正在關閉...")
    _running = False

signal.signal(signal.SIGINT,  _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


# ── Tick 處理 callback ──────────────────────────────────────
def on_tick_received(tick_data: dict):
    """
    每筆 Tick 進來時執行：
    1. 傳給 TickProcessor 聚合成分鐘K
    2. 如果分鐘K完成，計算指標並檢查警示（含完整 OHLCV + 技術指標）
    3. 高等級警示 → 同時傳送趨勢線圖
    4. TickProcessor 內建 GEM 偵測結果（indicators['gem']）→ 突破時推播計畫
    5. 每 CHART_INTERVAL_MINUTES 分鐘定時推一次趨勢線圖
    """
    global _last_chart_minute, _last_gem_minute, _last_gem_status

    price  = tick_data['price']
    volume = tick_data['volume']
    t      = tick_data['time']

    # 過濾試算揭示（開盤前試撮）
    if tick_data.get('simulate'):
        return

    logger.debug(f"Tick  {t}  價格:{price}  量:{volume}")

    # 傳給處理器
    minute_bar = processor.add_tick(price, volume)

    # 分鐘K完成時才計算指標
    if minute_bar:
        indicators = processor.get_indicators()
        if indicators:
            alerts = alert_engine.check(minute_bar, indicators)
            gem = indicators.get('gem')  # 高低點預測價位
            chart_sent_this_bar = False
            for alert in alerts:
                logger.info(f"觸發警示：{alert['name']} — {alert['message']}")
                notifier.send_alert(
                    alert,
                    gem=gem,
                    bar=minute_bar,
                    indicators=indicators,
                )  # 附帶完整 OHLCV + 技術指標 + 高低點預測
                # 高等級警示 → 附上趨勢線圖（每根K棒只傳一次，避免重複）
                if alert['level'] == 'high' and not chart_sent_this_bar:
                    logger.info("高等級警示，同步傳送趨勢線圖")
                    notifier.send_trendline_chart(
                        processor,
                        caption=(
                            f"📊 <b>警示觸發圖表</b>\n"
                            f"📌 {alert['name']}\n"
                            f"📝 {alert['message']}"
                        ),
                    )
                    chart_sent_this_bar = True

            # ── GEM 框型突破偵測（使用 TickProcessor 內建偵測結果）──────
            # indicators['gem'] 已由 TickProcessor.get_indicators() 計算完畢，
            # 直接取用即可，無需重複建立 RectangleDetector
            if gem and gem.get('status') in ('breakout_up', 'breakout_down') and gem.get('plan'):
                now = datetime.now()
                gem_key = now.strftime('%Y-%m-%d %H:%M')
                # 冷卻時間：同方向同狀態在 GEM_COOLDOWN_MINUTES 內只推一次
                cooldown_ok = (
                    _last_gem_minute is None or
                    _last_gem_status != gem['status'] or
                    (
                        datetime.strptime(gem_key, '%Y-%m-%d %H:%M') -
                        datetime.strptime(_last_gem_minute, '%Y-%m-%d %H:%M')
                    ).total_seconds() / 60 >= GEM_COOLDOWN_MINUTES
                )
                if cooldown_ok:
                    _last_gem_minute = gem_key
                    _last_gem_status = gem['status']
                    plan = gem['plan']
                    logger.info(
                        f"GEM 突破偵測 [{gem['status']}] "
                        f"TP1:{plan['tp1']:.0f} TP2:{plan['tp2']:.0f} SL:{plan['sl']:.0f}"
                    )
                    notifier.send_gem_plan(plan)
                    # GEM 突破時也附上趨勢線圖（若本根尚未推過）
                    if not chart_sent_this_bar:
                        notifier.send_trendline_chart(
                            processor,
                            caption=(
                                f"📊 <b>GEM 突破圖表</b>\n"
                                f"{'📈' if gem['status'] == 'breakout_up' else '📉'} "
                                f"{'向上突破' if gem['status'] == 'breakout_up' else '向下跌破'} "
                                f"{gem['resistance']:.0f}~{gem['support']:.0f}\n"
                                f"TP1: {plan['tp1']:.0f}  TP2: {plan['tp2']:.0f}  SL: {plan['sl']:.0f}"
                            ),
                        )
                        chart_sent_this_bar = True

            # 定時推送趨勢線圖（每 CHART_INTERVAL_MINUTES 分鐘）
            if CHART_INTERVAL_MINUTES > 0 and not chart_sent_this_bar:
                now = datetime.now()
                # 整除 N 分鐘的分鐘才推（例如 30 分鐘：09:00, 09:30, 10:00 ...）
                if now.minute % CHART_INTERVAL_MINUTES == 0:
                    chart_key = now.strftime('%Y-%m-%d %H:%M')
                    if chart_key != _last_chart_minute:
                        _last_chart_minute = chart_key
                        logger.info(f"定時推送趨勢線圖（每 {CHART_INTERVAL_MINUTES} 分鐘）")
                        notifier.send_trendline_chart(processor)


def on_best5_received(best5_data: dict):
    """收到五檔委託時（選擇性處理）"""
    # 可用於監控買賣掛單不均衡等條件
    pass


# ── 主程式 ──────────────────────────────────────────────────
def main():
    global processor, alert_engine, notifier

    logger.info("="*60)
    logger.info("台指期當沖監控系統 啟動")
    logger.info(f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)

    # 初始化各模組
    processor    = TickProcessor(
        gem_lookback=int(os.getenv('GEM_LOOKBACK_BARS', '60')),
        gem_breakout_buffer=float(os.getenv('GEM_BREAKOUT_BUFFER', '0.002')),
        gem_sl_offset=float(os.getenv('GEM_SL_OFFSET', '20')),
    )
    alert_engine = AlertEngine()
    notifier     = TelegramNotifier(
        bot_token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
        chat_id=os.getenv('TELEGRAM_CHAT_ID', ''),
    )
    # GEM 框型偵測由 TickProcessor 內建處理，
    # 可透過環境變數調整參數（TickProcessor 建構時傳入）：
    #   GEM_LOOKBACK_BARS / GEM_BREAKOUT_BUFFER / GEM_SL_OFFSET
    # 此處不再額外建立 RectangleDetector，避免重複計算

    # 測試 Telegram 連線
    if notifier.is_configured():
        notifier.send_message("台指期監控系統已啟動 ✅")
        logger.info("Telegram 通知已啟用")
    else:
        logger.warning("Telegram 未設定，警示只會顯示在 log")

    # 連線群益 API
    client = CapitalClient()

    try:
        logger.info("正在連線群益 API...")
        if not client.connect():
            logger.error("群益 API 登入失敗，請確認帳號密碼")
            return

        # 等待報價主機連線完成（OnConnection 3003 = Stocks ready）
        logger.info("正在連線報價主機...")
        if not client.login_quote():
            logger.error("報價主機連線失敗")
            client.disconnect()
            return

        # 等待商品資料下載（通常需要幾秒）
        logger.info("等待商品資料下載完成...")
        time.sleep(5)

        # 訂閱台指期近月 Tick + 五檔
        subscriber = FuturesSubscriber(client)
        success = subscriber.subscribe_txf(
            tick_callback=on_tick_received,
            best5_callback=on_best5_received,
        )

        if not success:
            logger.error("台指期訂閱失敗")
            client.disconnect()
            return

        logger.info("台指期 TX00 訂閱成功，開始監控...")
        logger.info("按 Ctrl+C 停止")

        # ── 主迴圈 ──────────────────────────────────────────
        while _running:
            time.sleep(1)

            # 每分鐘顯示狀態
            now = datetime.now()
            if now.second == 0:
                stats = processor.get_stats()
                logger.info(
                    f"狀態更新 | "
                    f"分鐘K數量: {stats['bar_count']} | "
                    f"最新價: {stats['last_price']} | "
                    f"累計量: {stats['total_volume']}"
                )

    except Exception as e:
        logger.error(f"主程式發生例外：{e}", exc_info=True)

    finally:
        logger.info("正在關閉連線...")
        client.disconnect()
        if notifier.is_configured():
            notifier.send_message("台指期監控系統已停止 🔴")
        logger.info("監控系統已關閉")


if __name__ == '__main__':
    main()
