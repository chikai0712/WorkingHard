"""
Telegram 通知模組

設定方式（.env）：
    TELEGRAM_BOT_TOKEN=你的 Bot Token（從 @BotFather 取得）
    TELEGRAM_CHAT_ID=你的 Chat ID（從 @userinfobot 取得）
"""

import logging
import requests
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramNotifier:
    LEVEL_EMOJI = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token.strip() if bot_token else ''
        self.chat_id   = chat_id.strip()   if chat_id   else ''
        self._api_url  = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    @staticmethod
    def _clear_proxy_env():
        """清除所有 proxy 環境變數，回傳備份（供還原用）"""
        import os
        _proxy_keys = [
            'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
            'ALL_PROXY', 'all_proxy', 'SOCKS_PROXY', 'SOCKS5_PROXY',
            'socks_proxy', 'socks5_proxy',
        ]
        return {k: os.environ.pop(k) for k in _proxy_keys if k in os.environ}

    @staticmethod
    def _restore_proxy_env(saved: dict):
        import os
        os.environ.update(saved)

    def send_message(self, text: str, parse_mode: str = 'HTML') -> bool:
        if not self.is_configured():
            logger.debug("Telegram 未設定，跳過推播")
            return False
        saved = self._clear_proxy_env()
        try:
            resp = requests.post(
                self._api_url,
                json={'chat_id': self.chat_id, 'text': text, 'parse_mode': parse_mode},
                timeout=10,
            )
            if resp.status_code == 200:
                return True
            logger.error(f"Telegram 推播失敗：HTTP {resp.status_code} — {resp.text}")
            return False
        except requests.exceptions.Timeout:
            logger.error("Telegram 推播逾時")
            return False
        except Exception as e:
            logger.error(f"Telegram 推播例外：{e}")
            return False
        finally:
            self._restore_proxy_env(saved)

    def send_alert(
        self,
        alert: Dict[str, Any],
        gem:   Dict = None,
        bar:   Dict = None,
        indicators: Dict = None,
    ) -> bool:
        """
        推播警示訊息，附帶完整價量資訊與高低點預測價位。

        Args:
            alert:      AlertEngine.check() 回傳的警示 dict
            gem:        indicators['gem']（高低點預測，可不傳）
            bar:        當根分鐘K dict（含 open/high/low/close/volume）
            indicators: get_indicators() 完整 dict（含所有技術指標）
        """
        level = alert.get('level', 'medium')
        emoji = self.LEVEL_EMOJI.get(level, '⚪')
        now   = alert.get('datetime', datetime.now().strftime('%Y-%m-%d %H:%M'))
        close = alert.get('close', 0)
        vol   = alert.get('volume', 0)

        # ── 分鐘K OHLCV（若有 bar 物件則補完整四價）────────
        if bar:
            o = bar.get('open',   close)
            h = bar.get('high',   close)
            l = bar.get('low',    close)
            c = bar.get('close',  close)
            v = bar.get('volume', vol)
        else:
            o = h = l = c = close
            v = vol

        ohlcv_line = (
            f"開 <b>{o:.0f}</b>  高 <b>{h:.0f}</b>  "
            f"低 <b>{l:.0f}</b>  收 <b>{c:.0f}</b>  "
            f"量 <b>{v}</b> 口"
        )

        # ── 技術指標（優先從完整 indicators 取，fallback 到 alert）
        ind = indicators or {}
        rsi  = ind.get('rsi')  or alert.get('rsi')
        macd = ind.get('macd') or alert.get('macd')
        msig = ind.get('macd_signal')
        mhst = ind.get('macd_hist')
        k    = ind.get('k')    or alert.get('k')
        d    = ind.get('d')    or alert.get('d')
        bbu  = ind.get('bb_upper')
        bbm  = ind.get('bb_mid')
        bbl  = ind.get('bb_lower')
        tdir = ind.get('trend_direction', '')

        ind_lines = []
        if rsi  is not None: ind_lines.append(f"RSI: <b>{rsi:.1f}</b>")
        if macd is not None:
            macd_str = f"MACD: <b>{macd:.1f}</b>"
            if msig is not None: macd_str += f" / Sig: {msig:.1f}"
            if mhst is not None:
                sign = '▲' if mhst > 0 else '▼'
                macd_str += f" / Hist: {sign}{abs(mhst):.1f}"
            ind_lines.append(macd_str)
        if k is not None and d is not None:
            ind_lines.append(f"KD: K=<b>{k:.1f}</b> D=<b>{d:.1f}</b>")
        if bbu is not None:
            ind_lines.append(f"BB: {bbl:.0f} ~ {bbu:.0f} (mid {bbm:.0f})")
        if tdir:
            dir_map = {'up': '↑ 上升', 'down': '↓ 下降', 'sideways': '↔ 橫盤'}
            ind_lines.append(f"趨勢: {dir_map.get(tdir, tdir)}")
        indicator_block = '\n'.join(f"   {l}" for l in ind_lines) if ind_lines else '   —'

        text = (
            f"{emoji} <b>台指期警示</b>"
            f"  <code>{now}</code>\n"
            f"{'─'*22}\n"
            f"📌 <b>{alert['name']}</b>\n"
            f"📝 {alert['message']}\n"
            f"{'─'*22}\n"
            f"📊 <b>價量</b>\n"
            f"   {ohlcv_line}\n"
            f"{'─'*22}\n"
            f"📈 <b>技術指標</b>\n"
            f"{indicator_block}"
        )

        # ── 附加高低點預測價位區塊 ────────────────────────────
        if gem is not None:
            try:
                from .price_target import format_price_levels
                price_block = format_price_levels(gem, current_price=c)
                if price_block:
                    text = text + '\n' + '─' * 22 + '\n' + price_block
            except Exception as _e:
                logger.warning(f"format_price_levels 發生錯誤：{_e}")

        return self.send_message(text)

    def send_photo(
        self,
        photo_bytes: bytes,
        caption: str = '',
        parse_mode: str = 'HTML',
    ) -> bool:
        """
        傳送圖片到 Telegram（用於趨勢線圖）

        Args:
            photo_bytes: PNG/JPG bytes
            caption:     圖片說明文字（支援 HTML）
        """
        if not self.is_configured():
            return False
        saved = self._clear_proxy_env()
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
            resp = requests.post(
                url,
                data={'chat_id': self.chat_id, 'caption': caption, 'parse_mode': parse_mode},
                files={'photo': ('chart.png', photo_bytes, 'image/png')},
                timeout=20,
            )
            if resp.status_code == 200:
                return True
            logger.error(f"Telegram 傳圖失敗：HTTP {resp.status_code} — {resp.text}")
            return False
        except Exception as e:
            logger.error(f"Telegram 傳圖例外：{e}")
            return False
        finally:
            self._restore_proxy_env(saved)

    def send_trendline_chart(
        self,
        processor,
        caption: str = '',
    ) -> bool:
        """
        一鍵產生趨勢線圖並傳送到 Telegram

        Args:
            processor: TickProcessor 實例
            caption:   圖片說明（預設自動產生）
        """
        try:
            from .trendline_chart import plot_trendlines
            png_bytes = plot_trendlines(processor, title='TXF 1-Min K + Trendlines')
            if not png_bytes:
                logger.warning("趨勢線圖產生失敗")
                return False

            if not caption:
                now = datetime.now().strftime('%H:%M')
                tl  = processor.get_trendlines()
                sup = f"{tl['support']['value']:.0f}" if tl['support'] else '-'
                res = f"{tl['resistance']['value']:.0f}" if tl['resistance'] else '-'
                direction = (
                    'Uptrend' if tl['support'] and tl['support']['slope'] > 0.5 else
                    'Downtrend' if tl['resistance'] and tl['resistance']['slope'] < -0.5 else
                    'Sideways'
                )
                caption = (
                    f"TXF Trendline Chart {now}\n"
                    f"{direction}\n"
                    f"Support: {sup}  Resistance: {res}"
                )

            return self.send_photo(png_bytes, caption=caption)

        except Exception as e:
            logger.error(f"send_trendline_chart 例外：{e}")
            return False

    def send_gem_plan(self, plan: Dict[str, Any]) -> bool:
        """
        傳送 GEM 框型突破交易計畫

        plan 格式（來自 price_target.calc_full_plan()）：
        {
            'direction':     'up' / 'down',
            'resistance':    float,
            'support':       float,
            'height':        float,
            'mid':           float,
            'tp1':           float,   # 框型一倍目標
            'tp2':           float,   # 翻亞當目標
            'sl':            float,   # 初始停損
            'breakout_price': float,
            'origin_price':   float,
            'adam_distance':  float,
        }
        """
        from capital_api.price_target import format_plan_message
        text = format_plan_message(plan)
        return self.send_message(text)

    def send_daily_summary(self, summary: Dict[str, Any]) -> bool:
        """
        每日盤後籌碼摘要推播

        summary 格式：
        {
            'date': '2026-03-19',
            'foreign_net': 3500,   # 外資期貨淨多單（口）
            'trust_net': -200,     # 投信期貨淨多單（口）
            'dealer_net': 100,     # 自營期貨淨多單（口）
            'foreign_oi': 45000,   # 外資未平倉（口）
            'pc_ratio': 0.85,      # Put/Call Ratio
            'margin_balance': 1234.5,  # 融資餘額（億）
            'close': 21000,        # 台指期收盤
            'volume': 85000,       # 全日成交量
        }
        """
        date   = summary.get('date', datetime.now().strftime('%Y-%m-%d'))
        close  = summary.get('close', 0)
        volume = summary.get('volume', 0)

        f_net  = summary.get('foreign_net', 0)
        t_net  = summary.get('trust_net', 0)
        d_net  = summary.get('dealer_net', 0)
        f_oi   = summary.get('foreign_oi', 0)
        pc     = summary.get('pc_ratio', 0)
        margin = summary.get('margin_balance', 0)

        def _sign(v):
            return '+' if v >= 0 else ''

        text = (
            f"📋 <b>台指期每日籌碼摘要</b> {date}\n"
            f"{'─'*24}\n"
            f"💰 收盤: <b>{close:.0f}</b>  成交量: {volume:,} 口\n"
            f"{'─'*24}\n"
            f"🏦 <b>三大法人期貨淨多單</b>\n"
            f"  外資: <b>{_sign(f_net)}{f_net:,}</b> 口\n"
            f"  投信: {_sign(t_net)}{t_net:,} 口\n"
            f"  自營: {_sign(d_net)}{d_net:,} 口\n"
            f"{'─'*24}\n"
            f"📌 外資未平倉: {f_oi:,} 口\n"
            f"📊 PC Ratio: {pc:.2f}\n"
            f"💳 融資餘額: {margin:.1f} 億"
        )
        return self.send_message(text)
