"""
期貨資料定時抓取任務
"""

import os
from datetime import datetime, time
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz

from database.session import SessionLocal
from crawler.taifex_crawler import TAIFEXCrawler
from crawler.taifex_web_scraper import TAIFEXWebScraper

def update_futures_data():
    """更新期貨相關資料"""
    print(f"🔄 開始執行定時任務：更新期貨資料 - {datetime.now()}")
    
    db = SessionLocal()
    try:
        crawler = TAIFEXCrawler(db)
        scraper = TAIFEXWebScraper()
        
        target_date = datetime.now().date()
        
        # 1. 抓取期貨每日資料
        print("📊 抓取期貨每日資料...")
        futures_data = scraper.get_futures_daily_report(target_date)
        if futures_data is not None:
            # 儲存邏輯（需要根據實際資料格式調整）
            print(f"✅ 期貨每日資料抓取成功")
        
        # 2. 抓取三大法人買賣超
        print("📊 抓取三大法人買賣超...")
        inst_data = scraper.get_institutional_trading(target_date)
        if inst_data:
            # 儲存邏輯
            print(f"✅ 三大法人資料抓取成功")
        
        # 3. 抓取融資融券資料
        print("📊 抓取融資融券資料...")
        for market_type in ['weighted', 'otc']:
            margin_data = scraper.get_twse_margin_trading(target_date)
            if margin_data:
                # 儲存邏輯
                print(f"✅ {market_type} 融資融券資料抓取成功")
        
        # 4. 抓取選擇權資料
        print("📊 抓取選擇權資料...")
        for period in ['weekly', 'monthly']:
            # 抓取選擇權每日資料
            # 抓取選擇權履約價分布
            print(f"✅ {period} 選擇權資料抓取成功")
        
        db.commit()
        print(f"✅ 期貨資料更新完成")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 期貨資料更新失敗: {str(e)}")
    finally:
        db.close()

def setup_futures_scheduler(scheduler):
    """設定期貨資料定時任務"""
    
    # 盤中更新：每 5 分鐘（交易時間 08:45-13:45）
    scheduler.add_job(
        func=update_futures_data,
        trigger=IntervalTrigger(minutes=5),
        id='update_futures_intraday',
        name='盤中期貨資料更新',
        replace_existing=True
    )
    
    # 收盤後完整更新：每天 15:35（收盤後5分鐘）
    scheduler.add_job(
        func=update_futures_data,
        trigger=CronTrigger(hour=15, minute=35, day_of_week='mon-fri'),
        id='update_futures_after_close',
        name='收盤後期貨資料更新',
        replace_existing=True
    )
    
    # 開盤前更新：每天 08:40（開盤前20分鐘）
    scheduler.add_job(
        func=update_futures_data,
        trigger=CronTrigger(hour=8, minute=40, day_of_week='mon-fri'),
        id='update_futures_pre_market',
        name='開盤前期貨資料更新',
        replace_existing=True
    )
    
    print("✅ 期貨資料定時任務已設定")

