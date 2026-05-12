#!/usr/bin/env python3
"""
使用 API 獲取匯率數據（替代網頁爬蟲）
支援多種免費匯率 API
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import pandas as pd
import os

class ExchangeRateAPI:
    """匯率 API 客戶端"""
    
    def __init__(self, api_provider: str = "exchangerate-api", api_key: Optional[str] = None):
        """
        初始化 API 客戶端
        
        Args:
            api_provider: API 提供者 ("exchangerate-api", "openexchangerates", "fixer")
            api_key: API Key（某些服務需要）
        """
        self.api_provider = api_provider
        self.api_key = api_key or os.getenv('EXCHANGE_RATE_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def get_rates(self, base_currency: str = "USD") -> Dict:
        """
        獲取匯率數據
        
        Args:
            base_currency: 基準貨幣（預設 USD）
        
        Returns:
            匯率數據字典
        """
        if self.api_provider == "exchangerate-api":
            return self._get_exchangerate_api(base_currency)
        elif self.api_provider == "openexchangerates":
            return self._get_openexchangerates(base_currency)
        elif self.api_provider == "fixer":
            return self._get_fixer(base_currency)
        else:
            raise ValueError(f"不支援的 API 提供者: {self.api_provider}")
    
    def _get_exchangerate_api(self, base_currency: str) -> Dict:
        """使用 ExchangeRate-API.com（無需 API Key）"""
        try:
            # 公開端點，無需 API Key
            url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
            
            print(f"🌐 正在從 ExchangeRate-API.com 獲取匯率數據...")
            print(f"   基準貨幣: {base_currency}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            print(f"✅ 成功獲取 {len(data.get('rates', {}))} 種貨幣匯率")
            
            return {
                'base': data.get('base', base_currency),
                'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
                'rates': data.get('rates', {}),
                'timestamp': datetime.now().isoformat(),
                'source': 'ExchangeRate-API.com'
            }
            
        except Exception as e:
            print(f"❌ 獲取匯率數據失敗: {e}")
            raise
    
    def _get_openexchangerates(self, base_currency: str) -> Dict:
        """使用 Open Exchange Rates（需要 API Key）"""
        if not self.api_key:
            raise ValueError("Open Exchange Rates 需要 API Key，請設置 EXCHANGE_RATE_API_KEY 環境變數")
        
        try:
            url = f"https://openexchangerates.org/api/latest.json"
            params = {
                'app_id': self.api_key,
                'base': base_currency
            }
            
            print(f"🌐 正在從 Open Exchange Rates 獲取匯率數據...")
            print(f"   基準貨幣: {base_currency}")
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            print(f"✅ 成功獲取 {len(data.get('rates', {}))} 種貨幣匯率")
            
            return {
                'base': data.get('base', base_currency),
                'date': datetime.fromtimestamp(data.get('timestamp', time.time())).strftime('%Y-%m-%d'),
                'rates': data.get('rates', {}),
                'timestamp': datetime.now().isoformat(),
                'source': 'Open Exchange Rates'
            }
            
        except Exception as e:
            print(f"❌ 獲取匯率數據失敗: {e}")
            raise
    
    def _get_fixer(self, base_currency: str) -> Dict:
        """使用 Fixer.io（需要 API Key）"""
        if not self.api_key:
            raise ValueError("Fixer.io 需要 API Key，請設置 EXCHANGE_RATE_API_KEY 環境變數")
        
        try:
            url = f"http://data.fixer.io/api/latest"
            params = {
                'access_key': self.api_key,
                'base': base_currency
            }
            
            print(f"🌐 正在從 Fixer.io 獲取匯率數據...")
            print(f"   基準貨幣: {base_currency}")
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('success', False):
                raise ValueError(f"API 錯誤: {data.get('error', {}).get('info', 'Unknown error')}")
            
            print(f"✅ 成功獲取 {len(data.get('rates', {}))} 種貨幣匯率")
            
            return {
                'base': data.get('base', base_currency),
                'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
                'rates': data.get('rates', {}),
                'timestamp': datetime.now().isoformat(),
                'source': 'Fixer.io'
            }
            
        except Exception as e:
            print(f"❌ 獲取匯率數據失敗: {e}")
            raise
    
    def convert_to_list(self, rates_data: Dict) -> List[Dict]:
        """
        將匯率數據轉換為列表格式
        
        Args:
            rates_data: API 返回的匯率數據
        
        Returns:
            匯率列表
        """
        rates_list = []
        base = rates_data.get('base', 'USD')
        rates = rates_data.get('rates', {})
        
        for currency, rate in rates.items():
            rates_list.append({
                'base_currency': base,
                'target_currency': currency,
                'rate': rate,
                'date': rates_data.get('date'),
                'timestamp': rates_data.get('timestamp'),
                'source': rates_data.get('source', 'Unknown')
            })
        
        return rates_list
    
    def save_to_json(self, rates_data: Dict, filename: Optional[str] = None):
        """保存為 JSON 格式"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"exchange_rates_api_{timestamp}.json"
        
        filepath = Path(filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(rates_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 已保存到: {filepath}")
    
    def save_to_csv(self, rates_list: List[Dict], filename: Optional[str] = None):
        """保存為 CSV 格式"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"exchange_rates_api_{timestamp}.csv"
        
        df = pd.DataFrame(rates_list)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        print(f"💾 已保存到: {filename}")
    
    def save_to_excel(self, rates_list: List[Dict], filename: Optional[str] = None):
        """保存為 Excel 格式"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"exchange_rates_api_{timestamp}.xlsx"
        
        df = pd.DataFrame(rates_list)
        df.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"💾 已保存到: {filename}")


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='使用 API 獲取匯率數據')
    parser.add_argument('--provider', choices=['exchangerate-api', 'openexchangerates', 'fixer'], 
                       default='exchangerate-api', help='API 提供者')
    parser.add_argument('--api-key', type=str, help='API Key（某些服務需要）')
    parser.add_argument('--base', type=str, default='USD', help='基準貨幣（預設 USD）')
    parser.add_argument('--format', choices=['json', 'csv', 'excel', 'all'], default='all', help='輸出格式')
    parser.add_argument('--output', type=str, help='輸出檔案名稱（不含副檔名）')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🌐 匯率 API 獲取工具")
    print("=" * 60)
    print(f"API 提供者: {args.provider}")
    print(f"基準貨幣: {args.base}")
    print("=" * 60)
    print()
    
    try:
        # 初始化 API 客戶端
        api = ExchangeRateAPI(api_provider=args.provider, api_key=args.api_key)
        
        # 獲取匯率數據
        rates_data = api.get_rates(base_currency=args.base)
        
        # 轉換為列表格式
        rates_list = api.convert_to_list(rates_data)
        
        print(f"\n✅ 成功獲取 {len(rates_list)} 種貨幣匯率")
        print("\n📊 數據預覽（前 10 項）:")
        for i, rate in enumerate(rates_list[:10], 1):
            print(f"   {i}. {rate['base_currency']}/{rate['target_currency']}: {rate['rate']}")
        if len(rates_list) > 10:
            print(f"   ... 還有 {len(rates_list) - 10} 種貨幣")
        
        # 保存數據
        base_name = args.output if args.output else None
        
        if args.format in ['json', 'all']:
            json_file = base_name + '.json' if base_name else None
            api.save_to_json(rates_data, json_file)
        
        if args.format in ['csv', 'all']:
            csv_file = base_name + '.csv' if base_name else None
            api.save_to_csv(rates_list, csv_file)
        
        if args.format in ['excel', 'all']:
            excel_file = base_name + '.xlsx' if base_name else None
            try:
                api.save_to_excel(rates_list, excel_file)
            except ImportError:
                print("⚠️  需要安裝 openpyxl 才能匯出 Excel: pip install openpyxl")
        
        print("\n✅ 完成！")
        
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

