#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 TWSE 即時行情 API
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.twse_realtime import TWSERealtimeClient
from datetime import date

def main():
    """測試 TWSE 即時 API"""
    print("🧪 測試 TWSE 即時行情 API")
    print("="*60)
    
    client = TWSERealtimeClient()
    
    # 測試股票：台積電 (2330)
    test_symbol = "2330"
    
    print(f"\n📊 測試股票: {test_symbol} (台積電)")
    print("-"*60)
    
    # 測試即時行情
    print("\n1. 測試即時行情（約 20 秒延遲）...")
    realtime_data = client.get_stock_realtime(test_symbol)
    
    if realtime_data:
        print("✅ 即時行情資料:")
        for key, value in realtime_data.items():
            print(f"   {key}: {value}")
    else:
        print("❌ 無法取得即時行情")
    
    # 測試每日行情
    print("\n2. 測試每日行情...")
    day_data = client.get_stock_day(test_symbol, date.today())
    
    if day_data:
        print("✅ 每日行情資料:")
        for key, value in day_data.items():
            print(f"   {key}: {value}")
    else:
        print("❌ 無法取得每日行情")
    
    # 測試多檔股票
    print("\n3. 測試多檔股票...")
    symbols = ["2330", "2317", "2454"]  # 台積電、鴻海、聯發科
    results = client.get_multiple_stocks_realtime(symbols)
    
    print(f"✅ 取得 {len([r for r in results.values() if r])}/{len(symbols)} 檔股票資料")
    for symbol, data in results.items():
        if data:
            print(f"   {symbol}: 收盤價 {data.get('close', 'N/A')}")
        else:
            print(f"   {symbol}: 失敗")
    
    print("\n" + "="*60)
    print("✅ 測試完成")

if __name__ == "__main__":
    main()

