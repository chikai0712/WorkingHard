#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期貨資料抓取腳本
用於手動觸發期貨資料抓取
"""

import sys
import os
from datetime import date, timedelta

# 添加父目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session import SessionLocal, init_db
from crawler.futures_data_fetcher import FuturesDataFetcher

def main():
    """主函數"""
    print("🚀 期貨資料抓取腳本")
    print("="*60)
    
    # 初始化資料庫
    init_db()
    print("✅ 資料庫已初始化\n")
    
    # 取得目標日期（預設今天，或從命令列參數取得）
    if len(sys.argv) > 1:
        try:
            target_date = date.fromisoformat(sys.argv[1])
        except:
            print(f"❌ 日期格式錯誤，請使用 YYYY-MM-DD 格式")
            return
    else:
        target_date = date.today()
    
    # 建立資料庫連線
    db = SessionLocal()
    try:
        # 建立抓取器
        fetcher = FuturesDataFetcher(db)
        
        # 抓取資料
        success_count, total_count = fetcher.fetch_and_save_all(target_date)
        
        print(f"\n📊 抓取結果:")
        print(f"   成功: {success_count}/{total_count}")
        
        if success_count == total_count:
            print("✅ 所有資料抓取成功！")
        elif success_count > 0:
            print("⚠️ 部分資料抓取成功")
        else:
            print("❌ 資料抓取失敗，請檢查網路連線和 API 狀態")
    
    finally:
        db.close()

if __name__ == "__main__":
    main()

