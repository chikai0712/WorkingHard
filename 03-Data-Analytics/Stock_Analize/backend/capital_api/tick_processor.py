"""
Tick 聚合處理器

功能：
- 將即時 Tick 聚合成分鐘K（OHLCV）
- 使用 pandas-ta 計算技術指標：MACD / RSI / KD / 布林通道
- 自動識別 Swing High / Low，計算上升支撐線與下降壓力線
"""

import logging
from collections import deque
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

import numpy as np
import pandas as pd

# GEM 價位計算（price_target 與 tick_processor 同層，用相對 import）
try:
    from .price_target import RectangleDetector
    _GEM_AVAILABLE = True
except ImportError:
    _GEM_AVAILABLE = False

# 嘗試載入 pandas-ta（Windows 推薦），fallback 到 ta（跨平台）
PANDAS_TA_AVAILABLE = False
TA_AVAILABLE = False

try:
    import pandas_ta as pta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    pass

if not PANDAS_TA_AVAILABLE:
    try:
        import ta as ta_lib
        TA_AVAILABLE = True
    except ImportError:
        logging.warning("請安裝技術指標套件：pip install ta  或  pip install pandas-ta")

logger = logging.getLogger(__name__)


class TickProcessor:
    """
    Tick → 分鐘K 聚合器 + 技術指標計算器

    每次收到 Tick 呼叫 add_tick()，
    當分鐘結束時回傳完整的分鐘K dict，否則回傳 None。
    """

    def __init__(
        self,
        max_bars: int = 200,
        gem_lookback: int = 60,
        gem_breakout_buffer: float = 0.002,
        gem_sl_offset: float = 20.0,
    ):
        """
        Args:
            max_bars:            保留最近幾根分鐘K（用於指標計算，預設 200）
            gem_lookback:        GEM 框型偵測回溯K棒數（預設 60）
            gem_breakout_buffer: GEM 突破確認緩衝比例（預設 0.2%）
            gem_sl_offset:       GEM 停損緩衝點數（預設 20 點）
        """
        self.max_bars = max_bars

        # 分鐘K 歷史（deque 自動限制長度）
        self._bars: deque = deque(maxlen=max_bars)

        # 當前分鐘累積中的 Tick
        self._current_minute: Optional[str] = None
        self._current_open:   Optional[float] = None
        self._current_high:   Optional[float] = None
        self._current_low:    Optional[float] = None
        self._current_close:  Optional[float] = None
        self._current_volume: int = 0

        # 統計
        self._total_volume: int = 0
        self._last_price:   Optional[float] = None

        # GEM 框型偵測器（內建於 processor，方便從外部直接呼叫）
        self._gem_detector: Optional[Any] = (
            RectangleDetector(
                lookback=gem_lookback,
                breakout_buffer=gem_breakout_buffer,
                sl_offset=gem_sl_offset,
            )
            if _GEM_AVAILABLE else None
        )

    def add_tick(self, price: float, volume: int,
                 timestamp: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        加入一筆 Tick，回傳完成的分鐘K（若分鐘尚未結束則回傳 None）

        Args:
            price: 成交價
            volume: 成交量（口數）
            timestamp: 時間（預設使用當下時間）

        Returns:
            完整的分鐘K dict，或 None（分鐘尚未結束）
        """
        if timestamp is None:
            timestamp = datetime.now()

        # 取得分鐘字串（精確到分鐘）
        minute_key = timestamp.strftime('%Y-%m-%d %H:%M')

        self._total_volume += volume
        self._last_price = price

        completed_bar = None

        if self._current_minute is None:
            # 第一筆 Tick，初始化當前分鐘
            self._start_new_minute(minute_key, price)

        elif minute_key != self._current_minute:
            # 進入新的分鐘，完成上一根 K 棒
            completed_bar = self._close_current_bar()
            self._start_new_minute(minute_key, price)

        # 更新當前分鐘
        self._current_high  = max(self._current_high,  price)
        self._current_low   = min(self._current_low,   price)
        self._current_close = price
        self._current_volume += volume

        return completed_bar

    def _start_new_minute(self, minute_key: str, price: float):
        """開始新的分鐘"""
        self._current_minute = minute_key
        self._current_open   = price
        self._current_high   = price
        self._current_low    = price
        self._current_close  = price
        self._current_volume = 0

    def _close_current_bar(self) -> Dict[str, Any]:
        """關閉當前分鐘，產生完整分鐘K"""
        bar = {
            'datetime': self._current_minute,
            'open':     self._current_open,
            'high':     self._current_high,
            'low':      self._current_low,
            'close':    self._current_close,
            'volume':   self._current_volume,
        }
        self._bars.append(bar)
        logger.debug(
            f"分鐘K完成 [{bar['datetime']}] "
            f"O:{bar['open']} H:{bar['high']} L:{bar['low']} "
            f"C:{bar['close']} V:{bar['volume']}"
        )
        return bar

    def get_indicators(self) -> Optional[Dict[str, Any]]:
        """
        計算最新技術指標（基於歷史分鐘K）
        支援 pandas-ta（Windows）和 ta（跨平台）兩種套件

        Returns:
            指標 dict，或 None（K棒數量不足）
        """
        if not PANDAS_TA_AVAILABLE and not TA_AVAILABLE:
            return None

        if len(self._bars) < 35:  # MACD Signal 最少需要 26+9=35 根
            logger.debug(f"K棒數量不足（{len(self._bars)}/35），跳過指標計算")
            return None

        try:
            df = pd.DataFrame(list(self._bars))
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime')

            indicators = {}

            if PANDAS_TA_AVAILABLE:
                # ── pandas-ta 版本（Windows 推薦）─────────────────
                macd = pta.macd(df['close'], fast=12, slow=26, signal=9)
                if macd is not None and not macd.empty:
                    indicators['macd']        = float(macd.iloc[-1, 0])
                    indicators['macd_signal'] = float(macd.iloc[-1, 1])
                    indicators['macd_hist']   = float(macd.iloc[-1, 2])

                rsi = pta.rsi(df['close'], length=14)
                if rsi is not None and len(rsi) > 0:
                    indicators['rsi'] = float(rsi.iloc[-1])

                stoch = pta.stoch(df['high'], df['low'], df['close'], k=9, d=3, smooth_k=3)
                if stoch is not None and not stoch.empty:
                    indicators['k'] = float(stoch.iloc[-1, 0])
                    indicators['d'] = float(stoch.iloc[-1, 1])

                bbands = pta.bbands(df['close'], length=20, std=2)
                if bbands is not None and not bbands.empty:
                    indicators['bb_upper'] = float(bbands.iloc[-1, 0])
                    indicators['bb_mid']   = float(bbands.iloc[-1, 1])
                    indicators['bb_lower'] = float(bbands.iloc[-1, 2])

            elif TA_AVAILABLE:
                # ── ta 套件版本（Mac/Linux 跨平台）────────────────
                import math

                def _safe(series):
                    """取最後一個非 NaN 值，全是 NaN 則回傳 None"""
                    val = series.iloc[-1]
                    return None if (val is None or (isinstance(val, float) and math.isnan(val))) else float(val)

                indicators['macd']        = _safe(ta_lib.trend.macd(df['close'], window_slow=26, window_fast=12))
                indicators['macd_signal'] = _safe(ta_lib.trend.macd_signal(df['close'], window_slow=26, window_fast=12, window_sign=9))
                indicators['macd_hist']   = _safe(ta_lib.trend.macd_diff(df['close'], window_slow=26, window_fast=12, window_sign=9))

                indicators['rsi'] = _safe(ta_lib.momentum.rsi(df['close'], window=14))

                indicators['k'] = _safe(ta_lib.momentum.stoch(df['high'], df['low'], df['close'],
                                                               window=9, smooth_window=3))
                indicators['d'] = _safe(ta_lib.momentum.stoch_signal(df['high'], df['low'], df['close'],
                                                                       window=9, smooth_window=3))

                bb = ta_lib.volatility.BollingerBands(df['close'], window=20, window_dev=2)
                indicators['bb_upper'] = _safe(bb.bollinger_hband())
                indicators['bb_mid']   = _safe(bb.bollinger_mavg())
                indicators['bb_lower'] = _safe(bb.bollinger_lband())

                # None 值清除（避免下游用 None 計算爆炸）
                indicators = {k: v for k, v in indicators.items() if v is not None}

            # 共用欄位
            indicators['close']     = float(df['close'].iloc[-1])
            indicators['volume']    = int(df['volume'].iloc[-1])
            indicators['bar_count'] = len(self._bars)

            # 趨勢線
            tl = self.get_trendlines()
            indicators['trendline_support']    = tl['support']['value']    if tl['support']    else None
            indicators['trendline_resistance'] = tl['resistance']['value'] if tl['resistance'] else None
            indicators['trend_direction'] = (
                'up'       if tl['support']    and tl['support']['slope']    > 0.5  else
                'down'     if tl['resistance'] and tl['resistance']['slope'] < -0.5 else
                'sideways'
            )

            # ── GEM 框型價位偵測 ──────────────────────────────────
            # 結果掛在 indicators['gem'] 供 AlertEngine / windows_monitor 直接使用
            indicators['gem'] = None
            if self._gem_detector is not None:
                try:
                    current_close = float(df['close'].iloc[-1])
                    gem_result = self._gem_detector.detect(df, current_close)
                    if gem_result is not None:
                        # 永遠回傳區間資訊；plan 僅在突破時才有值
                        gem_out: Dict[str, Any] = {
                            'status':     gem_result['status'],      # 'breakout_up' / 'breakout_down' / 'in_range'
                            'resistance': gem_result['resistance'],
                            'support':    gem_result['support'],
                            'height':     gem_result['rect']['height'],
                            'mid':        gem_result['rect']['mid'],
                            'plan':       gem_result.get('plan'),    # None if in_range
                        }
                        # 突破時額外攤平 plan 欄位方便直接讀取
                        if gem_out['plan']:
                            p = gem_out['plan']
                            gem_out.update({
                                'direction':      p['direction'],
                                'breakout_price': p['breakout_price'],
                                'origin_price':   p['origin_price'],
                                'tp1':            p['tp1'],
                                'tp2':            p['tp2'],
                                'sl':             p['sl'],
                                'adam_distance':  p['adam_distance'],
                            })
                        indicators['gem'] = gem_out
                        logger.debug(
                            f"GEM detect → status={gem_out['status']} "
                            f"R:{gem_out['resistance']:.0f} S:{gem_out['support']:.0f}"
                            + (
                                f" TP1:{gem_out['tp1']:.0f} TP2:{gem_out['tp2']:.0f} SL:{gem_out['sl']:.0f}"
                                if gem_out.get('tp1') else ''
                            )
                        )
                except Exception as _gem_err:
                    logger.error(f"GEM 偵測發生錯誤：{_gem_err}")

            return indicators

        except Exception as e:
            logger.error(f"計算技術指標時發生錯誤：{e}")
            return None

    # ── 趨勢線計算 ────────────────────────────────────────────

    def _find_swing_points(
        self, df: pd.DataFrame, window: int = 5
    ) -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
        """
        找擺動高點（Swing High）與擺動低點（Swing Low）

        Args:
            df: 分鐘K DataFrame（含 high / low / close 欄位）
            window: 左右各幾根作比較（預設 5）

        Returns:
            (swing_highs, swing_lows)
            每個元素為 (bar_index, price)
        """
        closes = df['close'].values
        highs  = df['high'].values
        lows   = df['low'].values
        n = len(closes)

        swing_highs: List[Tuple[int, float]] = []
        swing_lows:  List[Tuple[int, float]] = []

        for i in range(window, n - window):
            # Swing High：左右 window 根的 high 都比它低
            if (all(highs[i] >= highs[i - j] for j in range(1, window + 1)) and
                    all(highs[i] >= highs[i + j] for j in range(1, window + 1))):
                swing_highs.append((i, highs[i]))

            # Swing Low：左右 window 根的 low 都比它高
            if (all(lows[i] <= lows[i - j] for j in range(1, window + 1)) and
                    all(lows[i] <= lows[i + j] for j in range(1, window + 1))):
                swing_lows.append((i, lows[i]))

        return swing_highs, swing_lows

    def _fit_trendline(
        self, points: List[Tuple[int, float]], current_idx: int
    ) -> Optional[Dict[str, Any]]:
        """
        用最近 2–3 個擺動點線性回歸，外推到 current_idx

        Returns:
            {
                'value':     float,   # 趨勢線在 current_idx 的值
                'slope':     float,   # 斜率（正=上升, 負=下降）
                'points':    list,    # 用於繪圖的擺動點 [(idx, price), ...]
                'intercept': float,
            }
            或 None（點數不足）
        """
        if len(points) < 2:
            return None

        recent = points[-3:]  # 最近 3 個擺動點
        xs = np.array([p[0] for p in recent], dtype=float)
        ys = np.array([p[1] for p in recent], dtype=float)

        try:
            slope, intercept = np.polyfit(xs, ys, 1)
        except Exception:
            return None

        value = slope * current_idx + intercept
        return {
            'value':     float(value),
            'slope':     float(slope),
            'intercept': float(intercept),
            'points':    recent,
        }

    def get_trendlines(self, window: int = 5) -> Dict[str, Any]:
        """
        計算上升支撐線與下降壓力線

        Returns:
            {
                'support':    {'value', 'slope', 'intercept', 'points'} or None,
                'resistance': {'value', 'slope', 'intercept', 'points'} or None,
                'swing_highs': [(idx, price), ...],
                'swing_lows':  [(idx, price), ...],
                'bar_count': int,
            }
        """
        if len(self._bars) < window * 2 + 5:
            return {
                'support': None, 'resistance': None,
                'swing_highs': [], 'swing_lows': [],
                'bar_count': len(self._bars),
            }

        df = pd.DataFrame(list(self._bars))
        current_idx = len(df) - 1
        swing_highs, swing_lows = self._find_swing_points(df, window=window)

        support    = self._fit_trendline(swing_lows,  current_idx)
        resistance = self._fit_trendline(swing_highs, current_idx)

        return {
            'support':     support,
            'resistance':  resistance,
            'swing_highs': swing_highs,
            'swing_lows':  swing_lows,
            'bar_count':   len(self._bars),
        }

    # ── 統計與資料取得 ────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """取得基本統計資訊"""
        return {
            'bar_count':    len(self._bars),
            'last_price':   self._last_price,
            'total_volume': self._total_volume,
            'current_minute': self._current_minute,
        }

    def get_bars_df(self) -> pd.DataFrame:
        """取得歷史分鐘K DataFrame"""
        if not self._bars:
            return pd.DataFrame()
        return pd.DataFrame(list(self._bars))
