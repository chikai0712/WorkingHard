"""
群益 API 使用範例
示範如何登入並訂閱台指期即時報價
"""

import logging
import time
from client import CapitalClient
from futures_subscriber import FuturesSubscriber

# 設定 logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def on_quote_received(quote_data):
    """
    收到報價時的處理函式
    
    Args:
        quote_data: 報價資料字典
    """
    print(f"\n收到台指期報價:")
    print(f"  時間: {quote_data['timestamp']}")
    print(f"  商品: {quote_data['product']}")
    print(f"  成交價: {quote_data['price']}")
    print(f"  成交量: {quote_data['volume']}")
    print(f"  買價: {quote_data['bid']} (量: {quote_data['bid_volume']})")
    print(f"  賣價: {quote_data['ask']} (量: {quote_data['ask_volume']})")


def main():
    """主程式"""
    
    # 方法 1: 使用 with 語法 (自動連線/斷線)
    try:
        with CapitalClient() as client:
            # 建立訂閱器
            subscriber = FuturesSubscriber(client)
            
            # 訂閱台指期
            subscriber.subscribe_txf(callback=on_quote_received)
            
            # 持續接收報價 (按 Ctrl+C 停止)
            logger.info("開始接收台指期即時報價，按 Ctrl+C 停止...")
            
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("\n使用者中斷，正在關閉...")
    except Exception as e:
        logger.error(f"執行時發生錯誤: {e}")
    
    # 方法 2: 手動控制連線
    # client = CapitalClient()
    # 
    # if client.connect():
    #     if client.login_quote():
    #         subscriber = FuturesSubscriber(client)
    #         subscriber.subscribe_txf(callback=on_quote_received)
    #         
    #         try:
    #             while True:
    #                 time.sleep(1)
    #         except KeyboardInterrupt:
    #             pass
    #         
    #         subscriber.unsubscribe_all()
    #     
    #     client.disconnect()


if __name__ == '__main__':
    main()
