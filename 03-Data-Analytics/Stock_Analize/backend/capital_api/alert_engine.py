"""
警示規則引擎

支援的條件：
- 價格突破（上穿 / 下穿指定價位）
- 成交量異常（單分鐘成交量超過閾值）
- MACD 黃金交叉 / 死亡交叉
- RSI 超買（> 80）/ 超賣（< 20）
- KD 黃金交叉 / 死亡交叉
- 布林通道突破（突破上軌 / 下穿下軌）
- 自訂條件（傳入 lambda）
"""

import logging
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)


class AlertEngine:
    """
    警示規則引擎

    使用方式：
        engine = AlertEngine()
        engine.add_price_breakout(level=21000, direction='above')
        engine.add_rsi_alert(overbought=80, oversold=20)
        engine.add_macd_cross()
        engine.add_volume_spike(threshold=500)

        alerts = engine.check(bar, indicators)
        for alert in alerts:
            print(alert['message'])
    """

    def __init__(self):
        self._rules: List[Dict[str, Any]] = []
        self._prev_indicators: Optional[Dict[str, Any]] = None
        self._load_default_rules()

    def _load_default_rules(self):
        """載入預設規則"""
        self.add_macd_cross()
        self.add_rsi_alert(overbought=80, oversold=20)
        self.add_kd_cross()
        self.add_bollinger_breakout()
        self.add_volume_spike(threshold=1000)
        self.add_trendline_break()

    # ── 規則新增方法 ────────────────────────────────────────

    def add_price_breakout(self, level: float, direction: str = 'above', name: str = ''):
        """
        價格突破警示
        direction: 'above'=向上突破, 'below'=向下跌破
        """
        rule_name = name or f"價格{'突破' if direction == 'above' else '跌破'} {level}"
        self._rules.append({
            'type': 'price_breakout',
            'name': rule_name,
            'level': level,
            'direction': direction,
            'triggered_once': False,
        })
        logger.info(f"已加入規則：{rule_name}")

    def add_volume_spike(self, threshold: int = 500, name: str = ''):
        """成交量異常警示：單分鐘成交量超過閾值"""
        rule_name = name or f"成交量異常 > {threshold} 口"
        self._rules.append({'type': 'volume_spike', 'name': rule_name, 'threshold': threshold})
        logger.info(f"已加入規則：{rule_name}")

    def add_macd_cross(self, name: str = 'MACD 交叉'):
        """MACD 黃金交叉 / 死亡交叉"""
        self._rules.append({'type': 'macd_cross', 'name': name})
        logger.info(f"已加入規則：{name}")

    def add_rsi_alert(self, overbought: float = 80, oversold: float = 20, name: str = 'RSI'):
        """RSI 超買 / 超賣"""
        self._rules.append({
            'type': 'rsi', 'name': name,
            'overbought': overbought, 'oversold': oversold,
        })
        logger.info(f"已加入規則：{name} (超買>{overbought}, 超賣<{oversold})")

    def add_kd_cross(self, name: str = 'KD 交叉'):
        """KD 黃金交叉 / 死亡交叉"""
        self._rules.append({'type': 'kd_cross', 'name': name})
        logger.info(f"已加入規則：{name}")

    def add_bollinger_breakout(self, name: str = '布林通道突破'):
        """布林通道上軌突破 / 下軌跌破"""
        self._rules.append({'type': 'bollinger', 'name': name})
        logger.info(f"已加入規則：{name}")

    def add_trendline_break(
        self,
        tolerance_pct: float = 0.003,
        name_support: str = '趨勢線支撐跌破',
        name_resistance: str = '趨勢線壓力突破',
    ):
        """
        趨勢線突破警示

        Args:
            tolerance_pct: 接近趨勢線的容差比例（預設 0.3%，用於「測試趨勢線」預警）
        """
        self._rules.append({
            'type': 'trendline_break',
            'name_support':    name_support,
            'name_resistance': name_resistance,
            'tolerance_pct':   tolerance_pct,
            'support_triggered':    False,
            'resistance_triggered': False,
        })
        logger.info(f"已加入規則：趨勢線突破（容差 {tolerance_pct*100:.1f}%）")

    def add_custom(
        self,
        name: str,
        condition: Callable[[Dict, Dict, Optional[Dict]], bool],
        message_fn: Callable[[Dict, Dict], str],
    ):
        """
        自訂條件
        condition: fn(bar, indicators, prev_indicators) -> bool
        message_fn: fn(bar, indicators) -> str
        """
        self._rules.append({
            'type': 'custom', 'name': name,
            'condition': condition, 'message_fn': message_fn,
        })
        logger.info(f"已加入自訂規則：{name}")

    # ── 規則檢查 ────────────────────────────────────────────

    def check(self, bar: Dict[str, Any], indicators: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        檢查所有規則，回傳觸發的警示列表

        Returns:
            [{'name': str, 'message': str, 'level': str, 'data': dict}, ...]
        """
        triggered = []
        for rule in self._rules:
            try:
                alert = self._check_rule(rule, bar, indicators)
                if alert:
                    triggered.append(alert)
                    logger.info(f"警示觸發：{alert['name']} — {alert['message']}")
            except Exception as e:
                rule_name = rule.get('name') or rule.get('name_support', rule.get('type', '?'))
                logger.error(f"檢查規則 '{rule_name}' 時發生錯誤：{e}")

        self._prev_indicators = indicators.copy()
        return triggered

    def _check_rule(self, rule: Dict, bar: Dict, ind: Dict) -> Optional[Dict]:
        """檢查單一規則，回傳警示 dict 或 None"""
        prev  = self._prev_indicators
        t     = rule['type']
        name  = rule.get('name', rule.get('name_support', rule.get('type', '')))
        close = bar.get('close', 0)
        vol   = bar.get('volume', 0)

        # ── 價格突破 ────────────────────────────────────────
        if t == 'price_breakout':
            level     = rule['level']
            direction = rule['direction']
            if direction == 'above' and close > level and not rule.get('triggered_once'):
                rule['triggered_once'] = True
                return self._make_alert(name, f"價格突破 {level}，當前 {close:.0f}", 'high', bar, ind)
            elif direction == 'below' and close < level and not rule.get('triggered_once'):
                rule['triggered_once'] = True
                return self._make_alert(name, f"價格跌破 {level}，當前 {close:.0f}", 'high', bar, ind)
            # 重置：價格回到另一側後可再次觸發
            elif direction == 'above' and close < level:
                rule['triggered_once'] = False
            elif direction == 'below' and close > level:
                rule['triggered_once'] = False

        # ── 成交量異常 ───────────────────────────────────────
        elif t == 'volume_spike':
            if vol > rule['threshold']:
                return self._make_alert(
                    name, f"單分鐘成交量 {vol} 口（閾值 {rule['threshold']}）", 'medium', bar, ind
                )

        # ── MACD 交叉 ────────────────────────────────────────
        elif t == 'macd_cross':
            if not prev or 'macd' not in ind or 'macd' not in prev:
                return None
            macd_now  = ind.get('macd', 0)
            sig_now   = ind.get('macd_signal', 0)
            macd_prev = prev.get('macd', 0)
            sig_prev  = prev.get('macd_signal', 0)
            # 黃金交叉：MACD 從下穿越 Signal
            if macd_prev < sig_prev and macd_now > sig_now:
                return self._make_alert(name, f"MACD 黃金交叉，收盤 {close:.0f}", 'high', bar, ind)
            # 死亡交叉：MACD 從上穿越 Signal
            elif macd_prev > sig_prev and macd_now < sig_now:
                return self._make_alert(name, f"MACD 死亡交叉，收盤 {close:.0f}", 'high', bar, ind)

        # ── RSI ─────────────────────────────────────────────
        elif t == 'rsi':
            rsi = ind.get('rsi')
            if rsi is None:
                return None
            if rsi > rule['overbought']:
                return self._make_alert(name, f"RSI 超買 {rsi:.1f}（>{rule['overbought']}）", 'medium', bar, ind)
            elif rsi < rule['oversold']:
                return self._make_alert(name, f"RSI 超賣 {rsi:.1f}（<{rule['oversold']}）", 'medium', bar, ind)

        # ── KD 交叉 ──────────────────────────────────────────
        elif t == 'kd_cross':
            if not prev or 'k' not in ind or 'k' not in prev:
                return None
            k_now, d_now   = ind.get('k', 0), ind.get('d', 0)
            k_prev, d_prev = prev.get('k', 0), prev.get('d', 0)
            if k_prev < d_prev and k_now > d_now:
                return self._make_alert(name, f"KD 黃金交叉，K={k_now:.1f} D={d_now:.1f}", 'high', bar, ind)
            elif k_prev > d_prev and k_now < d_now:
                return self._make_alert(name, f"KD 死亡交叉，K={k_now:.1f} D={d_now:.1f}", 'high', bar, ind)

        # ── 布林通道 ─────────────────────────────────────────
        elif t == 'bollinger':
            upper = ind.get('bb_upper')
            lower = ind.get('bb_lower')
            if upper is None or lower is None:
                return None
            if close > upper:
                return self._make_alert(
                    name, f"突破布林上軌 {upper:.0f}，收盤 {close:.0f}", 'medium', bar, ind
                )
            elif close < lower:
                return self._make_alert(
                    name, f"跌破布林下軌 {lower:.0f}，收盤 {close:.0f}", 'medium', bar, ind
                )

        # ── 趨勢線突破 ────────────────────────────────────────
        elif t == 'trendline_break':
            tol  = rule['tolerance_pct']
            sup  = ind.get('trendline_support')
            res  = ind.get('trendline_resistance')

            # 上升支撐線跌破
            if sup is not None:
                if close < sup and not rule['support_triggered']:
                    rule['support_triggered'] = True
                    return self._make_alert(
                        rule['name_support'],
                        f"跌破上升支撐線 {sup:.0f}，收盤 {close:.0f}",
                        'high', bar, ind,
                    )
                elif close > sup * (1 + tol):
                    rule['support_triggered'] = False  # 重置
                # 接近支撐線預警（距離在容差內但尚未跌破）
                elif sup * (1 - tol) <= close <= sup and not rule['support_triggered']:
                    return self._make_alert(
                        rule['name_support'],
                        f"測試上升支撐線 {sup:.0f}（收盤 {close:.0f}，差 {close - sup:.0f}）",
                        'medium', bar, ind,
                    )

            # 下降壓力線突破
            if res is not None:
                if close > res and not rule['resistance_triggered']:
                    rule['resistance_triggered'] = True
                    return self._make_alert(
                        rule['name_resistance'],
                        f"突破下降壓力線 {res:.0f}，收盤 {close:.0f}",
                        'high', bar, ind,
                    )
                elif close < res * (1 - tol):
                    rule['resistance_triggered'] = False  # 重置
                # 接近壓力線預警
                elif res <= close <= res * (1 + tol) and not rule['resistance_triggered']:
                    return self._make_alert(
                        rule['name_resistance'],
                        f"測試下降壓力線 {res:.0f}（收盤 {close:.0f}，差 {res - close:.0f}）",
                        'medium', bar, ind,
                    )

        # ── 自訂條件 ─────────────────────────────────────────
        elif t == 'custom':
            if rule['condition'](bar, ind, prev):
                msg = rule['message_fn'](bar, ind)
                return self._make_alert(name, msg, 'medium', bar, ind)

        return None

    def _make_alert(
        self, name: str, message: str, level: str,
        bar: Dict, indicators: Dict
    ) -> Dict[str, Any]:
        """產生標準格式的警示 dict"""
        return {
            'name':     name,
            'message':  message,
            'level':    level,   # 'high' / 'medium' / 'low'
            'datetime': bar.get('datetime', ''),
            'close':    bar.get('close', 0),
            'volume':   bar.get('volume', 0),
            'rsi':      indicators.get('rsi'),
            'macd':     indicators.get('macd'),
            'k':        indicators.get('k'),
            'd':        indicators.get('d'),
        }
