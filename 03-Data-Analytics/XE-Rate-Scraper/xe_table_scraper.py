#!/usr/bin/env python3
"""
爬取 XE.com 公開匯率表格頁面
https://www.xe.com/currencytables/?from=TWD&date=2025-12-28
不需要登入！
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import pandas as pd
import re

class XETableScraper:
    """XE.com 匯率表格爬蟲"""
    
    BASE_URL = "https://www.xe.com/currencytables/"
    
    def __init__(self):
        """初始化爬蟲"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
    
    def scrape(self, base_currency: str = "TWD", date: Optional[str] = None) -> List[Dict]:
        """
        爬取匯率表格
        
        Args:
            base_currency: 基準貨幣（預設 TWD）
            date: 日期（格式：YYYY-MM-DD），如果為 None 則嘗試今天，失敗則使用昨天
        
        Returns:
            匯率列表
        """
        if date is None:
            # 嘗試今天，如果失敗則使用昨天
            date = datetime.now().strftime('%Y-%m-%d')
            dates_to_try = [date, (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')]
        else:
            dates_to_try = [date]
        
        for attempt_date in dates_to_try:
            url = f"{self.BASE_URL}?from={base_currency}&date={attempt_date}"
            
            print(f"🌐 正在訪問: {url}")
            print(f"   基準貨幣: {base_currency}")
            print(f"   日期: {attempt_date}")
            
            try:
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 404:
                    if len(dates_to_try) > 1 and attempt_date == dates_to_try[0]:
                        print(f"   ⚠️  日期 {attempt_date} 的數據不存在，嘗試使用昨天的數據...")
                        continue
                    else:
                        print(f"   ❌ 日期 {attempt_date} 的數據不存在")
                        return []
                
                response.raise_for_status()
                
                print("✅ 頁面載入成功")
                
                # 解析 HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找匯率表格
                rates = self._parse_table(soup, base_currency, attempt_date)
                
                if rates:
                    return rates
                else:
                    if len(dates_to_try) > 1 and attempt_date == dates_to_try[0]:
                        print("⚠️  未找到匯率數據，嘗試使用昨天的數據...")
                        continue
                    else:
                        print("⚠️  未找到匯率數據")
                        return []
                
            except Exception as e:
                if len(dates_to_try) > 1 and attempt_date == dates_to_try[0]:
                    print(f"   ⚠️  獲取 {attempt_date} 的數據失敗: {e}")
                    print(f"   嘗試使用昨天的數據...")
                    continue
                else:
                    print(f"❌ 爬取失敗: {e}")
                    import traceback
                    traceback.print_exc()
                    return []
        
        return []
    
    def _parse_table(self, soup: BeautifulSoup, base_currency: str, date: str) -> List[Dict]:
        """解析匯率表格"""
        rates = []
        
        # 查找表格（可能是 <table> 或包含表格的 <div>）
        table = soup.find('table')
        
        if not table:
            # 嘗試查找包含表格的其他元素
            table = soup.find('div', class_=re.compile(r'table', re.I))
        
        if not table:
            print("   ⚠️  未找到表格元素")
            return rates
        
        print(f"   ✅ 找到表格")
        
        # 查找所有行
        rows = table.find_all('tr')
        
        if not rows:
            print("   ⚠️  表格中沒有行")
            return rates
        
        print(f"   📊 找到 {len(rows)} 行數據")
        
        # 跳過表頭，處理數據行
        for row in rows[1:]:  # 跳過第一行（表頭）
            cells = row.find_all(['td', 'th'])
            
            if len(cells) < 3:
                continue
            
            try:
                # 提取貨幣代碼和名稱
                currency_cell = cells[0]
                currency_link = currency_cell.find('a')
                
                if currency_link:
                    currency_code = currency_link.text.strip()
                    # 嘗試從連結的 href 或 title 獲取名稱
                    currency_name = currency_link.get('title', '')
                    if not currency_name:
                        # 查找連結後的文字（通常是貨幣名稱）
                        next_sibling = currency_link.next_sibling
                        if next_sibling:
                            currency_name = next_sibling.strip()
                else:
                    # 如果沒有連結，直接取文字
                    currency_text = currency_cell.get_text(strip=True)
                    # 嘗試提取貨幣代碼（通常是前3個大寫字母）
                    currency_match = re.search(r'([A-Z]{3})', currency_text)
                    currency_code = currency_match.group(1) if currency_match else currency_text[:3]
                    # 提取貨幣名稱（貨幣代碼後的部分）
                    name_match = re.search(r'[A-Z]{3}\s+(.+)', currency_text)
                    currency_name = name_match.group(1).strip() if name_match else currency_text.replace(currency_code, '').strip()
                
                # 如果還是沒有名稱，嘗試從整個單元格文字中提取
                if not currency_name:
                    full_text = currency_cell.get_text(separator=' ', strip=True)
                    # 格式通常是 "USD US Dollar" 或 "USD"
                    parts = full_text.split()
                    if len(parts) > 1:
                        currency_name = ' '.join(parts[1:])
                    else:
                        currency_name = ''
                
                # 提取匯率（Units per TWD）
                units_per_base = None
                base_per_unit = None
                
                if len(cells) >= 2:
                    units_text = cells[1].get_text(strip=True)
                    units_per_base = self._parse_number(units_text)
                
                if len(cells) >= 3:
                    per_unit_text = cells[2].get_text(strip=True)
                    base_per_unit = self._parse_number(per_unit_text)
                
                if currency_code and (units_per_base is not None or base_per_unit is not None):
                    rate_data = {
                        'base_currency': base_currency,
                        'target_currency': currency_code,
                        'currency_name': currency_name,
                        'units_per_base': units_per_base,
                        'base_per_unit': base_per_unit,
                        'date': date,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'XE.com Currency Tables'
                    }
                    rates.append(rate_data)
                    
            except Exception as e:
                print(f"   ⚠️  解析行時出錯: {e}")
                continue
        
        return rates
    
    def _parse_alternative(self, soup: BeautifulSoup, base_currency: str, date: str) -> List[Dict]:
        """替代解析方法：從頁面中提取 JSON 數據"""
        rates = []
        
        # 查找包含 JSON 數據的 <script> 標籤
        scripts = soup.find_all('script')
        
        for script in scripts:
            script_text = script.string
            if not script_text:
                continue
            
            # 查找包含匯率數據的 JSON
            if 'currency' in script_text.lower() or 'rate' in script_text.lower():
                try:
                    # 嘗試提取 JSON
                    json_match = re.search(r'\{[^{}]*"rates"[^{}]*\}', script_text)
                    if json_match:
                        data = json.loads(json_match.group(0))
                        # 處理數據...
                        pass
                except:
                    pass
        
        return rates
    
    def _parse_number(self, text: str) -> Optional[float]:
        """解析數字文字"""
        if not text:
            return None
        
        # 移除逗號和其他格式字符
        text = text.replace(',', '').strip()
        
        try:
            return float(text)
        except ValueError:
            return None
    
    def save_to_json(self, rates: List[Dict], filename: Optional[str] = None):
        """保存為 JSON 格式"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"xe_table_rates_{timestamp}.json"
        
        filepath = Path(filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(rates, f, indent=2, ensure_ascii=False)
        
        print(f"💾 已保存到: {filepath}")
    
    def save_to_csv(self, rates: List[Dict], filename: Optional[str] = None):
        """保存為 CSV 格式"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"xe_table_rates_{timestamp}.csv"
        
        df = pd.DataFrame(rates)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        print(f"💾 已保存到: {filename}")
    
    def save_to_excel(self, rates: List[Dict], filename: Optional[str] = None):
        """保存為 Excel 格式"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"xe_table_rates_{timestamp}.xlsx"
        
        df = pd.DataFrame(rates)
        df.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"💾 已保存到: {filename}")
    
    def scrape_multiple_days(self, base_currency: str = "TWD", days: int = 30, 
                            end_date: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        爬取多天的匯率數據
        
        Args:
            base_currency: 基準貨幣（預設 TWD）
            days: 要爬取的天數（預設 30）
            end_date: 結束日期（格式：YYYY-MM-DD），如果為 None 則使用今天
        
        Returns:
            字典，key 為日期，value 為該日的匯率列表
        """
        if end_date is None:
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        all_rates = {}
        successful_days = 0
        failed_days = 0
        
        print(f"\n📅 開始爬取過去 {days} 天的匯率數據...")
        print(f"   基準貨幣: {base_currency}")
        print(f"   日期範圍: {(end_date - timedelta(days=days-1)).strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        print()
        
        for i in range(days):
            current_date = end_date - timedelta(days=i)
            date_str = current_date.strftime('%Y-%m-%d')
            
            print(f"[{i+1}/{days}] 正在爬取 {date_str} 的數據...", end=' ')
            
            rates = self.scrape(base_currency=base_currency, date=date_str)
            
            if rates:
                all_rates[date_str] = rates
                successful_days += 1
                print(f"✅ 成功獲取 {len(rates)} 種貨幣")
            else:
                failed_days += 1
                print(f"❌ 失敗")
            
            # 避免請求過於頻繁
            if i < days - 1:
                import time
                time.sleep(0.5)  # 每次請求間隔 0.5 秒
        
        print(f"\n📊 爬取完成: 成功 {successful_days} 天，失敗 {failed_days} 天")
        
        return all_rates
    
    def calculate_average_rates(self, all_rates: Dict[str, List[Dict]], 
                               base_currency: str = "TWD") -> List[Dict]:
        """
        計算多天匯率的平均值
        
        Args:
            all_rates: 多天的匯率數據字典
            base_currency: 基準貨幣
        
        Returns:
            包含平均匯率的列表
        """
        if not all_rates:
            return []
        
        # 收集所有貨幣的所有數據
        currency_data = {}  # {currency_code: {dates: [], rates: []}}
        
        for date, rates in all_rates.items():
            for rate in rates:
                currency = rate.get('target_currency')
                if not currency:
                    continue
                
                base_per_unit = rate.get('base_per_unit')
                if base_per_unit is None:
                    continue
                
                if currency not in currency_data:
                    currency_data[currency] = {
                        'currency_name': rate.get('currency_name', ''),
                        'dates': [],
                        'rates': []
                    }
                
                currency_data[currency]['dates'].append(date)
                currency_data[currency]['rates'].append(base_per_unit)
        
        # 計算平均值
        average_rates = []
        
        for currency, data in currency_data.items():
            if not data['rates']:
                continue
            
            rates = data['rates']
            avg_rate = sum(rates) / len(rates)
            min_rate = min(rates)
            max_rate = max(rates)
            
            # 計算標準差
            import statistics
            if len(rates) > 1:
                std_dev = statistics.stdev(rates)
            else:
                std_dev = 0.0
            
            average_rates.append({
                'base_currency': base_currency,
                'target_currency': currency,
                'currency_name': data['currency_name'],
                'average_rate': avg_rate,
                'min_rate': min_rate,
                'max_rate': max_rate,
                'std_deviation': std_dev,
                'data_points': len(rates),
                'date_range_start': min(data['dates']),
                'date_range_end': max(data['dates']),
                'timestamp': datetime.now().isoformat(),
                'source': 'XE.com Currency Tables (30-day average)'
            })
        
        # 按貨幣代碼排序
        average_rates.sort(key=lambda x: x['target_currency'])
        
        return average_rates


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='爬取 XE.com 公開匯率表格（無需登入）')
    parser.add_argument('--base', type=str, default='TWD', help='基準貨幣（預設 TWD）')
    parser.add_argument('--date', type=str, help='日期（格式：YYYY-MM-DD），預設為今天')
    parser.add_argument('--days', type=int, help='爬取多天並計算平均值（例如：30 表示過去30天）')
    parser.add_argument('--end-date', type=str, help='多天爬取的結束日期（格式：YYYY-MM-DD），預設為今天')
    parser.add_argument('--format', choices=['json', 'csv', 'excel', 'all'], default='all', help='輸出格式')
    parser.add_argument('--output', type=str, help='輸出檔案名稱（不含副檔名）')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🌐 XE.com 匯率表格爬蟲（無需登入）")
    print("=" * 60)
    
    scraper = XETableScraper()
    
    # 如果指定了 --days，則爬取多天並計算平均值
    if args.days:
        print(f"基準貨幣: {args.base}")
        print(f"計算天數: {args.days} 天平均")
        print("=" * 60)
        print()
        
        # 爬取多天數據
        all_rates = scraper.scrape_multiple_days(
            base_currency=args.base,
            days=args.days,
            end_date=args.end_date
        )
        
        if not all_rates:
            print("\n❌ 未能獲取任何匯率數據")
            return
        
        # 計算平均值
        print("\n📊 正在計算平均值...")
        average_rates = scraper.calculate_average_rates(all_rates, args.base)
        
        if not average_rates:
            print("\n❌ 無法計算平均值")
            return
        
        print(f"\n✅ 成功計算 {len(average_rates)} 種貨幣的 {args.days} 天平均匯率")
        print("\n📊 數據預覽（前 10 項）:")
        for i, rate in enumerate(average_rates[:10], 1):
            currency = rate.get('target_currency', 'N/A')
            name = rate.get('currency_name', '')
            avg = rate.get('average_rate', 'N/A')
            min_rate = rate.get('min_rate', 'N/A')
            max_rate = rate.get('max_rate', 'N/A')
            points = rate.get('data_points', 0)
            print(f"   {i}. {currency} ({name[:15]:15s}): 平均={avg:.6f}, 範圍=[{min_rate:.6f}, {max_rate:.6f}], 數據點={points}")
        if len(average_rates) > 10:
            print(f"   ... 還有 {len(average_rates) - 10} 種貨幣")
        
        # 保存數據
        base_name = args.output if args.output else f"xe_table_rates_avg_{args.days}days"
        
        if args.format in ['json', 'all']:
            json_file = base_name + '.json' if base_name else None
            scraper.save_to_json(average_rates, json_file)
        
        if args.format in ['csv', 'all']:
            csv_file = base_name + '.csv' if base_name else None
            scraper.save_to_csv(average_rates, csv_file)
        
        if args.format in ['excel', 'all']:
            excel_file = base_name + '.xlsx' if base_name else None
            try:
                scraper.save_to_excel(average_rates, excel_file)
            except ImportError:
                print("⚠️  需要安裝 openpyxl 才能匯出 Excel: pip install openpyxl")
        
    else:
        # 單日爬取（原有功能）
        print(f"基準貨幣: {args.base}")
        print(f"日期: {args.date or '今天'}")
        print("=" * 60)
        print()
        
        rates = scraper.scrape(base_currency=args.base, date=args.date)
        
        if not rates:
            print("\n❌ 未能獲取匯率數據")
            print("\n💡 提示:")
            print("   1. 檢查網路連接")
            print("   2. 檢查日期格式是否正確（YYYY-MM-DD）")
            print("   3. 檢查基準貨幣代碼是否正確")
            return
        
        print(f"\n✅ 成功獲取 {len(rates)} 種貨幣匯率")
        print("\n📊 數據預覽（前 10 項）:")
        for i, rate in enumerate(rates[:10], 1):
            currency = rate.get('target_currency', 'N/A')
            name = rate.get('currency_name', '')
            per_unit = rate.get('base_per_unit', 'N/A')
            print(f"   {i}. {currency} ({name[:20]}): {per_unit}")
        if len(rates) > 10:
            print(f"   ... 還有 {len(rates) - 10} 種貨幣")
        
        # 保存數據
        base_name = args.output if args.output else None
        
        if args.format in ['json', 'all']:
            json_file = base_name + '.json' if base_name else None
            scraper.save_to_json(rates, json_file)
        
        if args.format in ['csv', 'all']:
            csv_file = base_name + '.csv' if base_name else None
            scraper.save_to_csv(rates, csv_file)
        
        if args.format in ['excel', 'all']:
            excel_file = base_name + '.xlsx' if base_name else None
            try:
                scraper.save_to_excel(rates, excel_file)
            except ImportError:
                print("⚠️  需要安裝 openpyxl 才能匯出 Excel: pip install openpyxl")
    
    print("\n✅ 完成！")


if __name__ == '__main__':
    main()

