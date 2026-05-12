#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 API 回應格式腳本
用於查看實際的 API 回應格式，以便調整資料解析邏輯
"""

import sys
import os
import requests
from datetime import date, timedelta
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_twse_margin_trading(target_date=None):
    """測試證交所融資融券 API"""
    if target_date is None:
        target_date = date.today() - timedelta(days=1)  # 使用昨天，因為今天可能不是交易日
    
    url = "https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN"
    date_str = target_date.strftime('%Y%m%d')
    
    params = {
        'date': date_str,
        'response': 'json',
        'selectType': 'ALL'
    }
    
    print(f"📊 測試證交所融資融券 API ({date_str})...")
    print(f"URL: {url}")
    print(f"Params: {params}\n")
    
    try:
        response = requests.get(url, params=params, timeout=30, verify=False)
        print(f"狀態碼: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}\n")
        
        if response.status_code == 200:
            data = response.json()
            print("API 回應結構:")
            print(f"  stat: {data.get('stat')}")
            print(f"  title: {data.get('title')}")
            print(f"  fields: {data.get('fields', [])}")
            print(f"\n前3筆資料:")
            for i, row in enumerate(data.get('data', [])[:3]):
                print(f"  資料 {i+1}: {row[:10]}...")  # 只顯示前10個欄位
            
            # 儲存完整回應供參考
            with open(f'/tmp/twse_margin_{date_str}.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n完整回應已儲存至: /tmp/twse_margin_{date_str}.json")
        else:
            print(f"錯誤回應: {response.text[:500]}")
    except Exception as e:
        print(f"❌ 錯誤: {str(e)}")

def test_taifex_institutional(target_date=None):
    """測試 TAIFEX 三大法人 API"""
    if target_date is None:
        target_date = date.today() - timedelta(days=1)
    
    url = "https://www.taifex.com.tw/cht/3/futDataDown"
    date_str = target_date.strftime('%Y/%m/%d')
    
    params = {
        'down_type': '2',
        'queryStartDate': date_str,
        'queryEndDate': date_str
    }
    
    print(f"\n📊 測試 TAIFEX 三大法人 API ({date_str})...")
    print(f"URL: {url}")
    print(f"Params: {params}\n")
    
    try:
        response = requests.get(url, params=params, timeout=30, verify=False)
        response.encoding = 'big5'
        print(f"狀態碼: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}\n")
        
        if response.status_code == 200:
            # 顯示前500字元
            print("回應前500字元:")
            print(response.text[:500])
            print("\n...")
            
            # 儲存完整回應
            with open(f'/tmp/taifex_institutional_{target_date.strftime("%Y%m%d")}.txt', 'w', encoding='big5') as f:
                f.write(response.text)
            print(f"完整回應已儲存至: /tmp/taifex_institutional_{target_date.strftime('%Y%m%d')}.txt")
        else:
            print(f"錯誤回應: {response.text[:500]}")
    except Exception as e:
        print(f"❌ 錯誤: {str(e)}")

if __name__ == "__main__":
    print("="*60)
    print("🔍 API 回應格式測試")
    print("="*60 + "\n")
    
    # 測試證交所 API
    test_twse_margin_trading()
    
    # 測試 TAIFEX API
    test_taifex_institutional()
    
    print("\n" + "="*60)
    print("✅ 測試完成")
    print("="*60)

