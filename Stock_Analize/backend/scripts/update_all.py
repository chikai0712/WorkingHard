#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手動更新所有資料（股票 + 期貨）
"""

import sys
import os
from datetime import date, datetime
from dotenv import load_dotenv

# 將父目錄加入路徑，以便導入模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 載入環境變數
load_dotenv()

from database.session import SessionLocal, init_db
from crawler.stock_crawler import StockCrawler
from crawler.futures_data_fetcher import FuturesDataFetcher

def update_stocks():
    """更新股票資料"""
    print("\n" + "="*60)
    print("📊 更新股票資料...")
    print("="*60)
    
    # 檢查是否使用即時 API
    use_realtime = os.getenv("USE_TWSE_REALTIME", "False").lower() == "true"
    if use_realtime:
        print("📡 使用 TWSE 即時 API（約 20 秒延遲）")
    else:
        print("📡 使用 yfinance（15-20 分鐘延遲）")
    
    db = SessionLocal()
    try:
        crawler = StockCrawler(db, use_realtime=use_realtime)
        results = crawler.update_all_stocks()
        
        print(f"✅ 股票更新完成！")
        print(f"   總數：{results['total']}")
        print(f"   成功：{results['success']}")
        print(f"   失敗：{results['failed']}")
        
        return results['success'] > 0
    except Exception as e:
        print(f"❌ 股票更新失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def update_futures():
    """更新期貨資料（今天的資料）"""
    print("\n" + "="*60)
    print("📈 更新期貨資料...")
    print("="*60)
    
    db = SessionLocal()
    try:
        fetcher = FuturesDataFetcher(db)
        target_date = date.today()
        
        print(f"📅 目標日期: {target_date.strftime('%Y-%m-%d')}")
        print("-" * 60)
        
        success_count, total_count = fetcher.fetch_and_save_all(target_date)
        
        print(f"\n✅ 期貨資料更新完成！")
        print(f"   成功：{success_count}/{total_count}")
        
        return success_count > 0
    except Exception as e:
        print(f"❌ 期貨資料更新失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def main():
    """主函數"""
    print("\n" + "="*60)
    print("🚀 手動更新所有資料")
    print("="*60)
    print(f"⏰ 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 初始化資料庫
    init_db()
    
    # 更新股票資料
    stocks_ok = update_stocks()
    
    # 更新期貨資料
    futures_ok = update_futures()
    
    # 總結
    print("\n" + "="*60)
    print("📋 更新總結")
    print("="*60)
    print(f"股票資料: {'✅ 成功' if stocks_ok else '❌ 失敗'}")
    print(f"期貨資料: {'✅ 成功' if futures_ok else '❌ 失敗'}")
    print("="*60)
    
    if stocks_ok and futures_ok:
        print("\n✅ 所有資料更新完成！")
        return 0
    else:
        print("\n⚠️  部分資料更新失敗，請檢查日誌")
        return 1

if __name__ == "__main__":
    sys.exit(main())

