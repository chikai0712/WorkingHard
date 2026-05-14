"""
定時任務定義
"""

import os
from datetime import datetime, time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session import SessionLocal
from crawler.stock_crawler import StockCrawler

def update_stock_prices():
    """更新所有股票的價格資料"""
    # 檢查是否在交易時間內（如果設定了僅交易時間更新）
    if not is_trading_hours():
        print(f"⏸️  跳過更新：不在交易時間內 - {datetime.now()}")
        return
    
    print(f"🔄 開始執行定時任務：更新股票價格 - {datetime.now()}")
    
    db = SessionLocal()
    try:
        # 檢查是否使用即時資料來源
        use_realtime = os.getenv("USE_TWSE_REALTIME", "False").lower() == "true"
        
        if use_realtime:
            print("📡 使用 TWSE 即時 API（約 20 秒延遲）")
        else:
            print("📡 使用 yfinance（15-20 分鐘延遲）")
        
        crawler = StockCrawler(db, use_realtime=use_realtime)
        results = crawler.update_all_stocks()
        
        print(f"✅ 更新完成：成功 {results['success']}，失敗 {results['failed']}")
    except Exception as e:
        print(f"❌ 定時任務執行失敗: {str(e)}")
    finally:
        db.close()

def is_trading_hours() -> bool:
    """檢查是否在交易時間內"""
    trading_hours_only = os.getenv("TRADING_HOURS_ONLY", "True").lower() == "true"
    
    if not trading_hours_only:
        return True
    
    # 取得當前時間（台灣時間 UTC+8）
    taiwan_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(taiwan_tz)
    current_time = now.time()
    
    # 台股交易時間：09:00 - 13:30
    market_open = time(9, 0)
    market_close = time(13, 30)
    
    # 檢查是否為交易日（週一到週五）
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    
    if weekday < 5 and market_open <= current_time <= market_close:
        return True
    
    return False

def setup_scheduler() -> BackgroundScheduler:
    """設定並啟動定時任務"""
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Taipei'))
    
    # 取得更新間隔（分鐘）
    interval_minutes = int(os.getenv("UPDATE_INTERVAL_MINUTES", "5"))
    
    # 設定定時任務：每 N 分鐘更新一次（僅在交易時間）
    scheduler.add_job(
        func=update_stock_prices,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id='update_stock_prices',
        name='更新股票價格',
        replace_existing=True,
        # 可以加入 next_run_time 檢查，但 APScheduler 不直接支援條件觸發
        # 所以在任務函數內檢查
    )
    
    # 收盤後執行完整資料更新（每天 15:30）
    scheduler.add_job(
        func=update_stock_prices,
        trigger=CronTrigger(hour=15, minute=30, day_of_week='mon-fri'),
        id='daily_update_after_close',
        name='收盤後完整更新',
        replace_existing=True
    )
    
    # 開盤前預先更新（每天 08:50）
    scheduler.add_job(
        func=update_stock_prices,
        trigger=CronTrigger(hour=8, minute=50, day_of_week='mon-fri'),
        id='pre_market_update',
        name='開盤前更新',
        replace_existing=True
    )
    
    # 加入期貨資料更新任務
    try:
        from scheduler.futures_tasks import setup_futures_scheduler
        setup_futures_scheduler(scheduler)
    except Exception as e:
        print(f"⚠️ 設定期貨資料任務時發生錯誤: {str(e)}")
    
    return scheduler

