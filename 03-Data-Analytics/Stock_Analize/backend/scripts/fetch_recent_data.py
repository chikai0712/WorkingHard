"""
抓取最近幾天的期貨相關資料
用於補齊歷史資料或測試
"""

import sys
import os
from datetime import date, timedelta

# 將專案根目錄加入 Python 路徑
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, backend_dir)

from database.session import init_db, SessionLocal
from crawler.futures_data_fetcher import FuturesDataFetcher

def main():
    """抓取最近 N 天的資料"""
    init_db()
    
    db = SessionLocal()
    fetcher = FuturesDataFetcher(db)
    
    # 抓取最近7天的資料
    days = 7
    print(f"\n{'='*60}")
    print(f"🚀 開始抓取最近 {days} 天的期貨資料")
    print(f"{'='*60}\n")
    
    success_count = 0
    failed_count = 0
    
    for i in range(days):
        target_date = date.today() - timedelta(days=i)
        print(f"\n📅 日期: {target_date.strftime('%Y-%m-%d')}")
        print("-" * 60)
        
        try:
            # 抓取融資融券資料
            margin_data = fetcher.fetch_twse_margin_trading(target_date)
            if margin_data:
                if fetcher.save_margin_trading_data(margin_data):
                    print(f"  ✅ 融資融券資料已儲存")
                else:
                    print(f"  ❌ 融資融券資料儲存失敗")
                    failed_count += 1
            else:
                print(f"  ⚠️ 無法取得融資融券資料（可能非交易日）")
                failed_count += 1
            
            # 抓取三大法人資料
            inst_data = fetcher.fetch_taifex_institutional_trading(target_date)
            if inst_data:
                if fetcher.save_institutional_trading_data(inst_data):
                    print(f"  ✅ 三大法人資料已儲存")
                    success_count += 1
                else:
                    print(f"  ❌ 三大法人資料儲存失敗")
                    failed_count += 1
            else:
                print(f"  ⚠️ 無法取得三大法人資料（可能非交易日）")
                failed_count += 1
        
        except Exception as e:
            print(f"  ❌ 發生錯誤: {str(e)}")
            failed_count += 1
        
        # 避免請求過快
        import time
        if i < days - 1:
            time.sleep(1)
    
    db.close()
    
    print(f"\n{'='*60}")
    print(f"✅ 資料抓取完成")
    print(f"   成功: {success_count}/{days} 天")
    print(f"   失敗: {failed_count}/{days} 天")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()

