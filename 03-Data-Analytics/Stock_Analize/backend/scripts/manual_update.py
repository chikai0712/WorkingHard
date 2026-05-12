#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手動觸發資料抓取的腳本
"""

import sys
import os

# 將父目錄加入路徑，以便導入模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session import SessionLocal
from crawler.stock_crawler import StockCrawler

def main():
    """手動觸發資料抓取"""
    db = SessionLocal()
    try:
        print("="*60)
        print("🔄 開始手動更新股票資料...")
        print("="*60)
        
        crawler = StockCrawler(db)
        results = crawler.update_all_stocks()
        
        print("="*60)
        print(f"✅ 更新完成！")
        print(f"   總數：{results['total']}")
        print(f"   成功：{results['success']}")
        print(f"   失敗：{results['failed']}")
        print("="*60)
        
    except Exception as e:
        print(f"❌ 更新過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()

