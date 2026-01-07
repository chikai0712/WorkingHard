#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新增初始股票列表的腳本
"""

import sys
import os

# 將父目錄加入路徑，以便導入模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session import SessionLocal
from services.stock_service import StockService

def main():
    """新增初始股票列表"""
    db = SessionLocal()
    try:
        stock_service = StockService(db)
        
        # 台股列表
        stocks_tw = [
            {"symbol": "2330", "market": "TW", "name": "台積電", "industry": "半導體"},
            {"symbol": "2317", "market": "TW", "name": "鴻海", "industry": "電子製造"},
            {"symbol": "2454", "market": "TW", "name": "聯發科", "industry": "半導體"},
            {"symbol": "2308", "market": "TW", "name": "台達電", "industry": "電子零組件"},
            {"symbol": "2303", "market": "TW", "name": "聯電", "industry": "半導體"},
        ]
        
        # 美股列表
        stocks_us = [
            {"symbol": "AAPL", "market": "US", "name": "Apple Inc.", "industry": "科技"},
            {"symbol": "MSFT", "market": "US", "name": "Microsoft", "industry": "科技"},
            {"symbol": "GOOGL", "market": "US", "name": "Alphabet", "industry": "科技"},
            {"symbol": "TSLA", "market": "US", "name": "Tesla", "industry": "汽車"},
        ]
        
        all_stocks = stocks_tw + stocks_us
        
        print("="*60)
        print("📊 開始新增股票...")
        print("="*60)
        
        success_count = 0
        failed_count = 0
        
        for stock_data in all_stocks:
            try:
                # 檢查是否已存在
                existing = stock_service.get_stock_by_symbol(stock_data["symbol"])
                if existing:
                    print(f"⏭️  已存在：{stock_data['symbol']} - {stock_data['name']}")
                    continue
                
                stock_service.create_stock(**stock_data)
                print(f"✅ 已新增：{stock_data['symbol']} - {stock_data['name']} ({stock_data['market']})")
                success_count += 1
            except Exception as e:
                print(f"❌ 新增失敗 {stock_data['symbol']}: {str(e)}")
                failed_count += 1
        
        print("="*60)
        print(f"📊 新增完成：成功 {success_count}，失敗 {failed_count}，跳過 {len(all_stocks) - success_count - failed_count}")
        print("="*60)
        
    finally:
        db.close()

if __name__ == "__main__":
    main()

