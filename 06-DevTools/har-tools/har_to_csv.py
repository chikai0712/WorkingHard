#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HAR 文件轉 CSV 工具
將 HAR (HTTP Archive) 文件轉換為 CSV 格式
"""

import json
import csv
import sys
import os
from datetime import datetime

def parse_har_to_csv(har_file, csv_file):
    """將 HAR 文件轉換為 CSV"""
    
    # 讀取 HAR 文件
    with open(har_file, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
    
    # 準備 CSV 數據
    entries = har_data['log']['entries']
    
    # CSV 欄位
    fieldnames = [
        '序號',
        '請求時間',
        '請求方法',
        'URL',
        '狀態碼',
        '狀態文本',
        '請求大小(bytes)',
        '響應大小(bytes)',
        '總大小(bytes)',
        '耗時(ms)',
        'DNS時間(ms)',
        '連接時間(ms)',
        'SSL時間(ms)',
        '發送時間(ms)',
        '等待時間(ms)',
        '接收時間(ms)',
        '內容類型',
        '資源類型',
        '優先級',
        'IP地址',
        '服務器',
        '緩存狀態'
    ]
    
    # 寫入 CSV
    with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for idx, entry in enumerate(entries, 1):
            request = entry.get('request', {})
            response = entry.get('response', {})
            timings = entry.get('timings', {})
            
            # 解析時間
            started = entry.get('startedDateTime', '')
            if started:
                try:
                    dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
                    started = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            # 獲取內容類型
            content_type = ''
            for header in response.get('headers', []):
                if header.get('name', '').lower() == 'content-type':
                    content_type = header.get('value', '')
                    break
            
            # 獲取服務器
            server = ''
            for header in response.get('headers', []):
                if header.get('name', '').lower() == 'server':
                    server = header.get('value', '')
                    break
            
            # 計算大小
            request_size = request.get('headersSize', 0) + request.get('bodySize', 0)
            response_size = response.get('headersSize', 0) + response.get('bodySize', 0)
            total_size = request_size + response_size
            
            # 寫入行
            row = {
                '序號': idx,
                '請求時間': started,
                '請求方法': request.get('method', ''),
                'URL': request.get('url', ''),
                '狀態碼': response.get('status', ''),
                '狀態文本': response.get('statusText', ''),
                '請求大小(bytes)': request_size if request_size > 0 else '',
                '響應大小(bytes)': response_size if response_size > 0 else '',
                '總大小(bytes)': total_size if total_size > 0 else '',
                '耗時(ms)': round(entry.get('time', 0), 2),
                'DNS時間(ms)': round(timings.get('dns', -1), 2) if timings.get('dns', -1) >= 0 else '',
                '連接時間(ms)': round(timings.get('connect', -1), 2) if timings.get('connect', -1) >= 0 else '',
                'SSL時間(ms)': round(timings.get('ssl', -1), 2) if timings.get('ssl', -1) >= 0 else '',
                '發送時間(ms)': round(timings.get('send', -1), 2) if timings.get('send', -1) >= 0 else '',
                '等待時間(ms)': round(timings.get('wait', -1), 2) if timings.get('wait', -1) >= 0 else '',
                '接收時間(ms)': round(timings.get('receive', -1), 2) if timings.get('receive', -1) >= 0 else '',
                '內容類型': content_type,
                '資源類型': entry.get('_resourceType', ''),
                '優先級': entry.get('_priority', ''),
                'IP地址': entry.get('serverIPAddress', ''),
                '服務器': server,
                '緩存狀態': '命中' if entry.get('cache', {}) else '未命中'
            }
            
            writer.writerow(row)
    
    return len(entries)

def main():
    if len(sys.argv) < 2:
        print("用法: python3 har_to_csv.py <HAR文件> [輸出CSV文件]")
        print("範例: python3 har_to_csv.py input.har output.csv")
        sys.exit(1)
    
    har_file = sys.argv[1]
    
    # 如果沒有指定輸出文件，存到當前執行目錄
    if len(sys.argv) >= 3:
        csv_file = sys.argv[2]
    else:
        base_name = os.path.basename(har_file).rsplit('.', 1)[0] + '.csv'
        csv_file = os.path.join(os.getcwd(), base_name)
    
    print(f"正在轉換 HAR 文件...")
    print(f"輸入: {har_file}")
    print(f"輸出: {csv_file}")
    print()
    
    try:
        count = parse_har_to_csv(har_file, csv_file)
        print(f"✅ 轉換完成！")
        print(f"共處理 {count} 個請求")
        print(f"CSV 文件已保存: {csv_file}")
    except FileNotFoundError:
        print(f"❌ 錯誤: 找不到文件 {har_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ 錯誤: {har_file} 不是有效的 JSON 文件")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 錯誤: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
