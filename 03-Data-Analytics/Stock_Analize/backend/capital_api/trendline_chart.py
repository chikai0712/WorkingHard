"""
趨勢線圖表產生器

功能：
- 繪製分鐘K線 + 上升支撐線 + 下降壓力線 + Swing 高低點
- 輸出 PNG 圖檔或回傳 bytes（Telegram 傳圖用）
"""

import io
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .tick_processor import TickProcessor

logger = logging.getLogger(__name__)


def plot_trendlines(
    processor: 'TickProcessor',
    title: str = 'TXF 1-Min K + Trendlines',
    save_path: Optional[str] = None,
    show: bool = False,
) -> Optional[bytes]:
    """
    Plot 1-min candlestick chart with trendlines.

    Args:
        processor:  TickProcessor instance
        title:      Chart title
        save_path:  Optional path to save PNG file
        show:       Show interactive window (local debug only)

    Returns:
        PNG bytes for Telegram send_photo, or None if insufficient data
    """
    try:
        import matplotlib
        matplotlib.use('Agg')  # 非互動模式（無 GUI 環境也能用）
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import numpy as np
        import pandas as pd
    except ImportError:
        logger.error("請安裝 matplotlib 與 numpy：pip install matplotlib numpy")
        return None

    df = processor.get_bars_df()
    if df.empty or len(df) < 10:
        logger.warning("K 棒數量不足，無法繪圖")
        return None

    tl = processor.get_trendlines()
    swing_highs = tl['swing_highs']
    swing_lows  = tl['swing_lows']
    support     = tl['support']
    resistance  = tl['resistance']

    # ── 資料準備 ──────────────────────────────────────────────
    n = len(df)
    xs = range(n)
    closes = df['close'].values
    highs  = df['high'].values
    lows   = df['low'].values
    opens  = df['open'].values

    # X 軸標籤（每 10 根顯示一個時間）
    tick_step = max(1, n // 10)
    x_ticks = list(range(0, n, tick_step))
    x_labels = [str(df['datetime'].iloc[i])[-8:-3] for i in x_ticks]  # HH:MM

    # ── 建立圖表 ──────────────────────────────────────────────
    fig, (ax1, ax2) = plt.subplots(
        2, 1,
        figsize=(14, 8),
        gridspec_kw={'height_ratios': [3, 1]},
        facecolor='#1a1a2e',
    )
    fig.suptitle(title, color='white', fontsize=14, fontweight='bold', y=0.98)

    for ax in (ax1, ax2):
        ax.set_facecolor('#16213e')
        ax.tick_params(colors='#aaaacc')
        ax.spines[:].set_color('#334466')
        ax.grid(True, color='#223355', linewidth=0.5, linestyle='--')

    # ── 子圖 1：K 線 + 趨勢線 ─────────────────────────────────
    bar_width = 0.6
    for i in range(n):
        color = '#26a69a' if closes[i] >= opens[i] else '#ef5350'  # 漲綠跌紅
        # 實體
        ax1.bar(i, abs(closes[i] - opens[i]),
                bottom=min(opens[i], closes[i]),
                color=color, width=bar_width, alpha=0.85)
        # 影線
        ax1.plot([i, i], [lows[i], highs[i]], color=color, linewidth=0.8)

    # ── 繪製上升支撐線 ────────────────────────────────────────
    if support and len(support['points']) >= 2:
        slope     = support['slope']
        intercept = support['intercept']
        pts       = support['points']
        x0, x1 = pts[0][0], n - 1
        y0 = slope * x0 + intercept
        y1 = slope * x1 + intercept
        ax1.plot([x0, x1], [y0, y1],
                 color='#00e676', linewidth=1.8, linestyle='--',
                 label=f'Support ({support["value"]:.0f})')
        # Swing Low 標記
        for idx, price in swing_lows:
            ax1.scatter(idx, price, color='#00e676', s=60, zorder=5, marker='^')

    # ── 繪製下降壓力線 ────────────────────────────────────────
    if resistance and len(resistance['points']) >= 2:
        slope     = resistance['slope']
        intercept = resistance['intercept']
        pts       = resistance['points']
        x0, x1 = pts[0][0], n - 1
        y0 = slope * x0 + intercept
        y1 = slope * x1 + intercept
        ax1.plot([x0, x1], [y0, y1],
                 color='#ff5252', linewidth=1.8, linestyle='--',
                 label=f'Resistance ({resistance["value"]:.0f})')
        # Swing High 標記
        for idx, price in swing_highs:
            ax1.scatter(idx, price, color='#ff5252', s=60, zorder=5, marker='v')

    ax1.set_xlim(-1, n)
    ax1.set_xticks(x_ticks)
    ax1.set_xticklabels(x_labels, fontsize=8)
    ax1.set_ylabel('Price', color='#aaaacc')
    ax1.legend(loc='upper left', fontsize=8,
               facecolor='#223355', labelcolor='white', framealpha=0.8)

    # 右側最新價標籤
    last_close = closes[-1]
    ax1.annotate(
        f' {last_close:.0f}',
        xy=(n - 1, last_close),
        xytext=(n - 0.5, last_close),
        color='white', fontsize=9, fontweight='bold',
        va='center',
    )

    # ── 子圖 2：成交量 ────────────────────────────────────────
    volumes = df['volume'].values
    vol_colors = ['#26a69a' if closes[i] >= opens[i] else '#ef5350' for i in range(n)]
    ax2.bar(xs, volumes, color=vol_colors, width=bar_width, alpha=0.75)
    ax2.set_xlim(-1, n)
    ax2.set_xticks(x_ticks)
    ax2.set_xticklabels(x_labels, fontsize=8)
    ax2.set_ylabel('Vol', color='#aaaacc')

    # ── Trend direction summary ───────────────────────────────
    direction = 'Uptrend' if (support and support['slope'] > 0.5) else \
                'Downtrend' if (resistance and resistance['slope'] < -0.5) else \
                'Sideways'
    fig.text(0.01, 0.01, direction, color='#aaaacc', fontsize=10,
             transform=fig.transFigure)

    plt.tight_layout(rect=[0, 0.03, 1, 0.97])

    # ── 輸出 ──────────────────────────────────────────────────
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        logger.info(f"趨勢線圖已存檔：{save_path}")

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)

    if show:
        try:
            import subprocess, tempfile, os
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                f.write(buf.getvalue())
                tmp = f.name
            subprocess.run(['open', tmp])  # macOS；Windows 改 'start'
        except Exception:
            pass

    return buf.getvalue()
