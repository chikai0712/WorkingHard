"""
期貨資料定時任務
"""

import os
from datetime import datetime, date, timedelta
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session import SessionLocal
from crawler.futures_data_fetcher import FuturesDataFetcher
from database.models_futures import MarginTradingData

def update_futures_data():
    """更新期貨相關資料（融資融券、三大法人、期貨每日資料）"""
    print(f"🔄 開始執行定時任務：更新期貨資料 - {datetime.now()}")
    
    db = SessionLocal()
    try:
        fetcher = FuturesDataFetcher(db)
        
        # 抓取今天的資料
        target_date = date.today()
        success_count, total_count = fetcher.fetch_and_save_all(target_date)
        
        print(f"✅ 期貨資料更新完成：成功 {success_count}/{total_count}")
    except Exception as e:
        print(f"❌ 期貨資料更新失敗: {str(e)}")
    finally:
        db.close()

def cleanup_old_data():
    """清理超過30天的舊資料"""
    print(f"🧹 開始清理超過30天的舊資料 - {datetime.now()}")
    
    db = SessionLocal()
    try:
        # 計算30天前的日期
        cutoff_date = date.today() - timedelta(days=30)
        
        # 清理融資融券資料
        deleted_count = db.query(MarginTradingData).filter(
            MarginTradingData.date < cutoff_date
        ).delete()
        
        db.commit()
        
        print(f"✅ 清理完成：刪除 {deleted_count} 筆超過30天的融資融券資料")
        
        # TODO: 清理其他期貨相關資料表
        # - FuturesDailyData
        # - InstitutionalTradingData
        # - FuturesOpenInterest
        # - OptionsDailyData
        # - OptionsStrikeData
        
    except Exception as e:
        db.rollback()
        print(f"❌ 清理舊資料失敗: {str(e)}")
    finally:
        db.close()

def setup_futures_scheduler(scheduler):
    """設定期貨資料相關的定時任務"""
    taiwan_tz = pytz.timezone('Asia/Taipei')
    
    # 檢查是否啟用每小時更新
    hourly_update_enabled = os.getenv("HOURLY_FUTURES_UPDATE", "True").lower() == "true"
    
    if hourly_update_enabled:
        # 每小時更新一次期貨資料
        scheduler.add_job(
            func=update_futures_data,
            trigger=IntervalTrigger(hours=1),
            id='hourly_futures_update',
            name='每小時更新期貨資料',
            replace_existing=True
        )
        print("✅ 期貨資料定時任務已設定")
        print("   - 每小時更新期貨資料")
    else:
        # 每天收盤後抓取資料（15:30，週一到週五）
        scheduler.add_job(
            func=update_futures_data,
            trigger=CronTrigger(hour=15, minute=30, day_of_week='mon-fri', timezone=taiwan_tz),
            id='daily_futures_update',
            name='每日期貨資料更新（收盤後）',
            replace_existing=True
        )
        print("✅ 期貨資料定時任務已設定")
        print("   - 每日 15:30 更新期貨資料（收盤後）")
    
    # 每天凌晨清理舊資料（02:00）
    scheduler.add_job(
        func=cleanup_old_data,
        trigger=CronTrigger(hour=2, minute=0, timezone=taiwan_tz),
        id='cleanup_old_futures_data',
        name='清理超過30天的舊資料',
        replace_existing=True
    )
    print("   - 每日 02:00 清理超過30天的舊資料")

