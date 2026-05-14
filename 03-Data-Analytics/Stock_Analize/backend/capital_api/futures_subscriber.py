"""
台指期即時報價訂閱器
基於官方 CapitalAPI_2/PythonExampleV2/Quote/Quote.py 改寫

核心修正：
- 補完 COM 事件處理器（OnNotifyTicksLONG、OnNotifyBest5LONG）
- 使用正確的台指期代碼 TX00（近月通用）
- 使用 comtypes.client.GetEvents 正確註冊事件
"""

import logging
from typing import Callable, Optional, Dict, Any
from datetime import datetime

try:
    import comtypes.client
    COMTYPES_AVAILABLE = True
except ImportError:
    COMTYPES_AVAILABLE = False

logger = logging.getLogger(__name__)


class _SKQuoteLibEvent:
    """
    群益報價事件處理器
    由 FuturesSubscriber 內部使用，將 COM 事件轉換為 Python callback
    """

    def __init__(self, tick_callback: Optional[Callable] = None,
                 best5_callback: Optional[Callable] = None):
        self.tick_callback = tick_callback
        self.best5_callback = best5_callback

    def OnConnection(self, nKind, nCode):
        """連線狀態變更"""
        status_map = {
            3001: "Connected — 報價連線成功",
            3002: "DisConnected — 報價已斷線",
            3003: "Stocks ready — 商品資料下載完成",
            3021: "Connect Error — 連線錯誤",
        }
        msg = status_map.get(nKind, f"未知狀態 {nKind}")
        logger.info(f"[OnConnection] {msg}")

    def OnNotifyServerTime(self, sHour, sMinute, sSecond, nTotal):
        """報價主機時間（每秒觸發，可用於確認連線存活）"""
        pass

    def OnNotifyTicksLONG(self, sMarketNo, nIndex, nPtr,
                          nDate, nTimehms, nTimemillismicros,
                          nBid, nAsk, nClose, nQty, nSimulate):
        """
        即時 Tick（成交明細）

        nTimehms: HHMMSS 整數（例如 133045 = 13:30:45）
        nClose / 100.0 = 成交價
        nQty = 成交量（口數）
        nSimulate: 0=一般揭示 1=試算揭示
        """
        try:
            t = str(nTimehms).zfill(6)
            hour   = int(t[0:2])
            minute = int(t[2:4])
            sec    = int(t[4:6])
            millisec = nTimemillismicros // 1000

            tick_data = {
                'timestamp':  datetime.now().isoformat(),
                'date':       str(nDate),
                'time':       f"{hour:02d}:{minute:02d}:{sec:02d}.{millisec:03d}",
                'price':      nClose / 100.0,
                'volume':     nQty,
                'bid':        nBid / 100.0,
                'ask':        nAsk / 100.0,
                'simulate':   nSimulate == 1,
                'market_no':  sMarketNo,
            }

            if self.tick_callback:
                self.tick_callback(tick_data)

        except Exception as e:
            logger.error(f"[OnNotifyTicksLONG] 處理 Tick 時發生錯誤：{e}")

    def OnNotifyHistoryTicksLONG(self, sMarketNo, nStockidx, nPtr,
                                  lDate, lTimehms, lTimemillismicros,
                                  nBid, nAsk, nClose, nQty, nSimulate):
        """歷史 Tick（訂閱後補送的歷史資料，忽略）"""
        pass

    def OnNotifyBest5LONG(self, sMarketNo, nStockidx,
                          nBestBid1, nBestBidQty1,
                          nBestBid2, nBestBidQty2,
                          nBestBid3, nBestBidQty3,
                          nBestBid4, nBestBidQty4,
                          nBestBid5, nBestBidQty5,
                          nExtendBid, nExtendBidQty,
                          nBestAsk1, nBestAskQty1,
                          nBestAsk2, nBestAskQty2,
                          nBestAsk3, nBestAskQty3,
                          nBestAsk4, nBestAskQty4,
                          nBestAsk5, nBestAskQty5,
                          nExtendAsk, nExtendAskQty,
                          nSimulate):
        """五檔委託（買賣各五檔價格與量）"""
        try:
            best5_data = {
                'timestamp': datetime.now().isoformat(),
                'simulate':  nSimulate == 1,
                'bids': [
                    {'price': nBestBid1 / 100.0, 'qty': nBestBidQty1},
                    {'price': nBestBid2 / 100.0, 'qty': nBestBidQty2},
                    {'price': nBestBid3 / 100.0, 'qty': nBestBidQty3},
                    {'price': nBestBid4 / 100.0, 'qty': nBestBidQty4},
                    {'price': nBestBid5 / 100.0, 'qty': nBestBidQty5},
                ],
                'asks': [
                    {'price': nBestAsk1 / 100.0, 'qty': nBestAskQty1},
                    {'price': nBestAsk2 / 100.0, 'qty': nBestAskQty2},
                    {'price': nBestAsk3 / 100.0, 'qty': nBestAskQty3},
                    {'price': nBestAsk4 / 100.0, 'qty': nBestAskQty4},
                    {'price': nBestAsk5 / 100.0, 'qty': nBestAskQty5},
                ],
            }

            if self.best5_callback:
                self.best5_callback(best5_data)

        except Exception as e:
            logger.error(f"[OnNotifyBest5LONG] 處理五檔時發生錯誤：{e}")

    def OnNotifyQuoteLONG(self, sMarketNo, nIndex):
        """即時報價更新（整體報價，非 Tick）"""
        pass

    def OnNotifyKLineData(self, bstrStockNo, bstrData):
        """K線資料回傳"""
        pass


class FuturesSubscriber:
    """
    台指期貨即時報價訂閱器

    使用方式：
        def on_tick(tick_data):
            print(f"成交價: {tick_data['price']} 量: {tick_data['volume']}")

        with CapitalClient() as client:
            sub = FuturesSubscriber(client)
            sub.subscribe_txf(tick_callback=on_tick)

            import time
            while True:
                time.sleep(1)
    """

    # 台指期近月合約通用代碼
    TXF_NEAR_MONTH = "TX00"

    def __init__(self, client):
        """
        Args:
            client: CapitalClient 實例（已完成 connect + login_quote）
        """
        self.client = client
        self._event_handler = None   # COM 事件處理器物件
        self._event_conn = None      # comtypes 事件連接（必須保留引用，否則 GC 會釋放）
        self.is_subscribed = False

    def subscribe_txf(
        self,
        tick_callback:  Optional[Callable[[Dict[str, Any]], None]] = None,
        best5_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        product_code:   str = TXF_NEAR_MONTH,
        page_no:        int = 0,
    ) -> bool:
        """
        訂閱台指期即時報價（Tick + 五檔委託）

        Args:
            tick_callback:  收到 Tick 時呼叫，參數格式見 _SKQuoteLibEvent.OnNotifyTicksLONG
            best5_callback: 收到五檔時呼叫，參數格式見 _SKQuoteLibEvent.OnNotifyBest5LONG
            product_code:   商品代碼（預設 TX00 = 台指期近月）
            page_no:        Page 編號（預設 0）

        Returns:
            bool: 訂閱是否成功
        """
        if not self.client.is_quote_connected:
            logger.error("請先確認 CapitalClient 已連線報價主機（login_quote）")
            return False

        try:
            # 建立事件處理器
            self._event_handler = _SKQuoteLibEvent(
                tick_callback=tick_callback,
                best5_callback=best5_callback,
            )

            # 向 skQ 註冊事件（必須保留 _event_conn 引用，否則事件會停止觸發）
            self._event_conn = comtypes.client.GetEvents(
                self.client.skQ, self._event_handler
            )

            # 訂閱 Tick + 五檔
            psPageNo, nCode = self.client.skQ.SKQuoteLib_RequestTicks(
                page_no, product_code
            )

            if nCode == 0:
                self.is_subscribed = True
                logger.info(f"已訂閱 {product_code} Tick + 五檔（Page {psPageNo}）")
                return True
            else:
                err = self.client.get_error_message(nCode)
                logger.error(f"訂閱失敗：{err}（代碼：{nCode}）")
                return False

        except Exception as e:
            logger.error(f"訂閱台指期時發生例外：{e}")
            return False

    def unsubscribe(self, product_code: str = TXF_NEAR_MONTH):
        """取消訂閱"""
        try:
            if self.client.skQ:
                nCode = self.client.skQ.SKQuoteLib_CancelRequestTicks(product_code)
                logger.info(f"已取消訂閱 {product_code}")
            self.is_subscribed = False
            self._event_conn = None
            self._event_handler = None
        except Exception as e:
            logger.error(f"取消訂閱時發生例外：{e}")
