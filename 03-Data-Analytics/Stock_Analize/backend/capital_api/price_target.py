"""
GEM 價位計算模組

支援：
  1. 框型價位計算 (Rectangle Analysis)
     - 向上突破目標 = 阻力位 + 區間高度
     - 向下跌破目標 = 支撐位 - 區間高度

  2. 翻亞當投射 (Adam Projection)
     - 目標價 = 突破點 + (突破點 - 起漲/起跌低點)

  3. 自動偵測（從分鐘K歷史資料）
     - 找近期震盪區間（高低點）
     - 偵測是否有突破並計算目標
"""

import logging
from typing import Dict, Any, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# 核心計算函式
# ══════════════════════════════════════════════════════════════════

def calc_rectangle(
    resistance: float,
    support: float,
) -> Dict[str, Any]:
    """
    框型價位計算

    Args:
        resistance: 阻力位（區間高點）
        support:    支撐位（區間低點）

    Returns:
        {
            'height':      區間高度,
            'mid':         框型中線,
            'tp_up':       向上突破目標 = 阻力位 + H,
            'tp_down':     向下跌破目標 = 支撐位 - H,
            'sl_up':       做多停損 = 框型中線（或支撐下20）,
            'sl_down':     做空停損 = 框型中線（或阻力上20）,
        }
    """
    if resistance <= support:
        raise ValueError(f"阻力位 ({resistance}) 必須大於支撐位 ({support})")

    h   = resistance - support
    mid = (resistance + support) / 2

    return {
        'resistance': resistance,
        'support':    support,
        'height':     h,
        'mid':        mid,
        'tp_up':      resistance + h,      # 向上目標
        'tp_down':    support - h,          # 向下目標
        'sl_up':      mid,                  # 做多停損（框型中線）
        'sl_down':    mid,                  # 做空停損（框型中線）
    }


def calc_adam(
    breakout_price: float,
    origin_price: float,
) -> Dict[str, Any]:
    """
    翻亞當投射 (Adam Theory Projection)

    以突破點為軸，對起漲/起跌點做鏡射

    Args:
        breakout_price: 突破確認價位
        origin_price:   起漲低點（做多）或起跌高點（做空）

    Returns:
        {
            'target':   翻亞當目標價,
            'distance': 突破點距起點的距離（點數）,
            'direction': 'up' or 'down',
        }
    """
    distance  = breakout_price - origin_price
    target    = breakout_price + distance
    direction = 'up' if distance > 0 else 'down'

    return {
        'target':    target,
        'distance':  abs(distance),
        'direction': direction,
        'breakout':  breakout_price,
        'origin':    origin_price,
    }


def calc_full_plan(
    resistance:    float,
    support:       float,
    breakout_price: float,
    origin_price:  float,
    sl_offset:     float = 20.0,
) -> Dict[str, Any]:
    """
    完整 GEM 交易計畫：框型 + 翻亞當 + 停損建議

    Args:
        resistance:     阻力位
        support:        支撐位
        breakout_price: 突破確認價位
        origin_price:   起漲低點（做多）or 起跌高點（做空）
        sl_offset:      停損在支撐/阻力外加的點數（預設 20）

    Returns:
        完整交易計畫 dict（可直接餵給 send_alert / send_message）
    """
    rect  = calc_rectangle(resistance, support)
    adam  = calc_adam(breakout_price, origin_price)
    direction = adam['direction']

    if direction == 'up':
        sl = support - sl_offset
    else:
        sl = resistance + sl_offset

    return {
        # 區間
        'resistance':    resistance,
        'support':       support,
        'height':        rect['height'],
        'mid':           rect['mid'],
        # 目標
        'tp1':           rect['tp_up']   if direction == 'up' else rect['tp_down'],
        'tp2':           adam['target'],
        # 停損
        'sl':            sl,
        # 元資料
        'direction':     direction,
        'breakout_price': breakout_price,
        'origin_price':   origin_price,
        'adam_distance':  adam['distance'],
    }


def format_plan_message(plan: Dict[str, Any]) -> str:
    """
    把 calc_full_plan 結果格式化為 Telegram HTML 訊息

    Args:
        plan: calc_full_plan() 的回傳值

    Returns:
        HTML 格式的 Telegram 訊息字串
    """
    direction_txt = '向上突破 📈' if plan['direction'] == 'up' else '向下跌破 📉'

    return (
        f"🎯 <b>GEM 價位計算報告</b>\n"
        f"{'─'*24}\n"
        f"<b>當前區間：</b> {plan['resistance']:.0f} ~ {plan['support']:.0f}\n"
        f"<b>區間大小：</b> {plan['height']:.0f} 點\n"
        f"<b>框型中線：</b> {plan['mid']:.0f}\n"
        f"{'─'*24}\n"
        f"<b>突破方向：</b> {direction_txt}\n"
        f"<b>突破確認：</b> {plan['breakout_price']:.0f}\n"
        f"<b>起漲/起跌：</b> {plan['origin_price']:.0f}\n"
        f"{'─'*24}\n"
        f"🏹 <b>TP1 (框型一倍)：</b> <b>{plan['tp1']:.0f}</b>\n"
        f"🚀 <b>TP2 (翻亞當)：</b>   <b>{plan['tp2']:.0f}</b>\n"
        f"🛑 <b>SL (初始停損)：</b>  <b>{plan['sl']:.0f}</b>\n"
        f"{'─'*24}\n"
        f"⚠️ <i>GEM 警語：確認收盤站上突破點才算有效，"
        f"回破立即出場。到達 TP1 後停損移至成本 +50 保本。</i>"
    )


def format_price_levels(
    gem: Dict[str, Any],
    current_price: Optional[float] = None,
) -> str:
    """
    不論是否突破，都能格式化輸出當前高低點預測價位。
    供 send_alert() 附加在每則警示訊息末尾。

    Args:
        gem:           indicators['gem'] 的值
                       （來自 TickProcessor.get_indicators()）
        current_price: 最新成交價（選填，用於顯示與各關鍵價的距離）

    Returns:
        Telegram HTML 片段字串
    """
    if gem is None:
        return ''

    status    = gem.get('status', 'in_range')
    resist    = gem.get('resistance', 0)
    support   = gem.get('support', 0)
    height    = gem.get('height', 0)
    mid       = gem.get('mid', 0)

    # ── 計算潛在目標（不管是否突破都顯示）──────────────────
    tp_up   = resist + height   # 向上框型目標
    tp_down = support - height  # 向下框型目標

    # 狀態標籤
    if status == 'breakout_up':
        status_tag = '📈 <b>向上突破中</b>'
    elif status == 'breakout_down':
        status_tag = '📉 <b>向下跌破中</b>'
    else:
        status_tag = '↔️ 震盪區間中'

    # 距離標示（若有當前價）
    def _dist(price: float) -> str:
        if current_price is None:
            return ''
        diff = price - current_price
        sign = '+' if diff >= 0 else ''
        return f" <i>({sign}{diff:.0f})</i>"

    lines = [
        f"📌 <b>價位預測</b>  {status_tag}",
        f"{'─'*22}",
        f"🔴 阻力：<b>{resist:.0f}</b>{_dist(resist)}",
        f"🟡 中線：{mid:.0f}{_dist(mid)}",
        f"🟢 支撐：<b>{support:.0f}</b>{_dist(support)}",
        f"{'─'*22}",
        f"🏹 上方目標：<b>{tp_up:.0f}</b>{_dist(tp_up)}",
        f"🏹 下方目標：<b>{tp_down:.0f}</b>{_dist(tp_down)}",
    ]

    # 突破時額外顯示 GEM 計畫的精確 TP/SL
    if gem.get('tp1') is not None:
        direction_txt = '做多' if gem['direction'] == 'up' else '做空'
        lines += [
            f"{'─'*22}",
            f"⚡ GEM {direction_txt}計畫",
            f"   突破確認：{gem['breakout_price']:.0f}",
            f"   TP1：<b>{gem['tp1']:.0f}</b>  TP2：<b>{gem['tp2']:.0f}</b>",
            f"   SL：<b>{gem['sl']:.0f}</b>",
        ]

    return '\n'.join(lines)


# ══════════════════════════════════════════════════════════════════
# 自動偵測（從分鐘K DataFrame）
# ══════════════════════════════════════════════════════════════════

class RectangleDetector:
    """
    從分鐘K歷史自動偵測近期震盪區間並判斷是否突破

    修復項目（v2）：
      1. 用百分位數（90/10）取代 max/min，避免長影線誇大區間
      2. min_touches 實際驗證高低點觸碰次數
      3. 連續突破狀態追蹤：記住上次突破方向，避免重複警示

    使用方式：
        detector = RectangleDetector(lookback=60)
        result = detector.detect(bars_df, current_close)
        if result:
            plan = result['plan']
            print(format_plan_message(plan))
    """

    def __init__(
        self,
        lookback:        int   = 60,    # 回溯幾根K棒找區間
        min_touches:     int   = 2,     # 高低點各至少幾次碰到才算有效區間
        breakout_buffer: float = 0.002, # 突破確認緩衝（0.2%）
        sl_offset:       float = 20.0,  # 停損緩衝點數
        touch_tolerance: float = 0.001, # 碰觸容差（0.1%），判定是否「碰到」關鍵價
    ):
        self.lookback        = lookback
        self.min_touches     = min_touches
        self.breakout_buffer = breakout_buffer
        self.sl_offset       = sl_offset
        self.touch_tolerance = touch_tolerance

        # 狀態記憶
        self._plan: Optional[Dict[str, Any]] = None
        self._last_status: Optional[str] = None  # 修復3：追蹤上次突破方向

    # ── 內部輔助 ──────────────────────────────────────────────────

    def _count_touches(self, series: pd.Series, level: float) -> int:
        """計算 series 中有幾根 K 棒碰觸到 level（含容差）"""
        tol = level * self.touch_tolerance
        return int(((series - level).abs() <= tol).sum())

    def _find_levels(
        self, recent: pd.DataFrame
    ) -> Optional[Tuple[float, float]]:
        """
        修復1：用 90/10 百分位取代 max/min，過濾長影線干擾。
        修復2：驗證高低點各至少被碰觸 min_touches 次。

        Returns:
            (resistance, support) 或 None（區間無效）
        """
        resistance = float(recent['high'].quantile(0.90))
        support    = float(recent['low'].quantile(0.10))

        # 碰觸次數驗證
        resist_touches = self._count_touches(recent['high'], resistance)
        support_touches = self._count_touches(recent['low'], support)

        if resist_touches < self.min_touches or support_touches < self.min_touches:
            logger.debug(
                f"[RectangleDetector] 區間無效 — "
                f"阻力碰觸:{resist_touches}次 支撐碰觸:{support_touches}次 "
                f"(需 >= {self.min_touches}次)"
            )
            return None

        return resistance, support

    # ── 主要偵測方法 ───────────────────────────────────────────────

    def detect(
        self,
        df:            pd.DataFrame,
        current_close: float,
    ) -> Optional[Dict[str, Any]]:
        """
        分析近期 K 棒，偵測框型與突破

        Args:
            df:            分鐘K DataFrame（含 open/high/low/close/volume）
            current_close: 最新收盤價

        Returns:
            None：資料不足或無有效區間
            dict：{
                'status':          'breakout_up' / 'breakout_down' / 'in_range',
                'resistance':      float,
                'support':         float,
                'is_new_breakout': bool,   # 修復3：True 表示本次是新突破
                'plan':            dict（calc_full_plan 結果），僅突破時有值
                'rect':            dict（calc_rectangle 結果），區間內也有值
            }
        """
        if len(df) < self.lookback:
            return None

        # 取最近 lookback 根
        recent = df.iloc[-self.lookback:]

        # 修復1+2：用百分位 + 碰觸驗證取得有效關鍵價
        levels = self._find_levels(recent)
        if levels is None:
            return None

        resistance, support = levels
        height = resistance - support

        # 區間太小（少於 50 點）不處理
        if height < 50:
            return None

        rect = calc_rectangle(resistance, support)

        # ── 找起漲/起跌點（近期最低/最高） ───────────────────
        origin_long  = float(recent['low'].tail(20).min())   # 做多：近20根低點
        origin_short = float(recent['high'].tail(20).max())  # 做空：近20根高點

        buf_up   = resistance * (1 + self.breakout_buffer)
        buf_down = support    * (1 - self.breakout_buffer)

        # ── 向上突破 ─────────────────────────────────────────
        if current_close > buf_up:
            # 修復3：判斷是否為新突破（上次不是向上突破才算新的）
            is_new = self._last_status != 'breakout_up'
            self._last_status = 'breakout_up'

            plan = calc_full_plan(
                resistance=resistance,
                support=support,
                breakout_price=current_close,
                origin_price=origin_long,
                sl_offset=self.sl_offset,
            )
            self._plan = plan

            if is_new:
                logger.info(
                    f"[RectangleDetector] 新向上突破 "
                    f"阻力:{resistance:.0f} 突破:{current_close:.0f} "
                    f"TP1:{plan['tp1']:.0f} TP2:{plan['tp2']:.0f}"
                )
            return {
                'status':          'breakout_up',
                'resistance':      resistance,
                'support':         support,
                'is_new_breakout': is_new,
                'rect':            rect,
                'plan':            plan,
            }

        # ── 向下跌破 ─────────────────────────────────────────
        elif current_close < buf_down:
            # 修復3：判斷是否為新突破
            is_new = self._last_status != 'breakout_down'
            self._last_status = 'breakout_down'

            plan = calc_full_plan(
                resistance=resistance,
                support=support,
                breakout_price=current_close,
                origin_price=origin_short,
                sl_offset=self.sl_offset,
            )
            self._plan = plan

            if is_new:
                logger.info(
                    f"[RectangleDetector] 新向下跌破 "
                    f"支撐:{support:.0f} 突破:{current_close:.0f} "
                    f"TP1:{plan['tp1']:.0f} TP2:{plan['tp2']:.0f}"
                )
            return {
                'status':          'breakout_down',
                'resistance':      resistance,
                'support':         support,
                'is_new_breakout': is_new,
                'rect':            rect,
                'plan':            plan,
            }

        # ── 在區間內 ─────────────────────────────────────────
        # 修復3：回到區間內，重置突破狀態，允許下次重新偵測
        self._last_status = 'in_range'
        return {
            'status':          'in_range',
            'resistance':      resistance,
            'support':         support,
            'is_new_breakout': False,
            'rect':            rect,
            'plan':            None,
        }

    def reset(self) -> None:
        """手動重置狀態（換月合約或盤前初始化時呼叫）"""
        self._plan        = None
        self._last_status = None
        logger.info("[RectangleDetector] 狀態已重置")

    def get_current_plan(self) -> Optional[Dict[str, Any]]:
        """取得最近一次偵測到的交易計畫"""
        return self._plan
