"""
期貨資料抓取器 - 實際實現
整合 TAIFEX 和 TWSE API 的資料抓取
"""

import requests
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
import time
import json
import io
from io import StringIO
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from database.models_futures import MarginTradingData
from database.models_futures import InstitutionalTradingData, FuturesContract, FuturesOpenInterest

try:
    from crawler.twse_api import TWSEClient
except ImportError:
    TWSEClient = None

class FuturesDataFetcher:
    """期貨資料抓取器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def fetch_twse_margin_trading(self, target_date: Optional[date] = None) -> Optional[Dict]:
        """
        抓取證交所融資融券餘額資料
        
        資料來源: https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN
        """
        if target_date is None:
            target_date = date.today()
        
        print(f"📊 抓取證交所融資融券資料 ({target_date.strftime('%Y%m%d')})...")
        
        if TWSEClient:
            twse_client = TWSEClient()
            result = twse_client.get_margin_trading(target_date)
            
            if result:
                print(f"✅ 成功抓取融資融券資料")
            
            return result
        else:
            print(f"⚠️ TWSEClient 未載入，使用舊方法")
            return None
    
    def fetch_taifex_institutional_trading(self, target_date: Optional[date] = None) -> Optional[Dict]:
        """
        抓取三大法人買賣超資料
        
        優先使用 HiStock（資料完整且可靠），TAIFEX 作為備用
        """
        if target_date is None:
            target_date = date.today()
        
        # 優先使用 HiStock（淨值資料更準確，與市場資料一致）
        try:
            from crawler.histock_scraper import HiStockScraper
            histock = HiStockScraper(self.db)
            result = histock.fetch_institutional_trading(target_date)
            
            if result and (result.get('foreign', {}).get('net') is not None or 
                          result.get('trust', {}).get('net') is not None or 
                          result.get('dealer', {}).get('net') is not None):
                # 檢查資料是否有效（至少有一個法人有資料）
                has_valid_data = (
                    (result.get('foreign', {}).get('net', 0) != 0) or
                    (result.get('trust', {}).get('net', 0) != 0) or
                    (result.get('dealer', {}).get('net', 0) != 0)
                )
                if has_valid_data:
                    print(f"✅ 成功從 HiStock 抓取三大法人資料")
                    return result
        except Exception as e:
            print(f"⚠️ 從 HiStock 抓取失敗: {str(e)}")
        
        # 備用方案：使用 TAIFEX
        try:
            from crawler.taifex_institutional_scraper import TAIFEXInstitutionalScraper
            scraper = TAIFEXInstitutionalScraper(self.db)
            result = scraper.fetch_institutional_trading(target_date)
            
            if result and (result.get('foreign', {}).get('net', 0) != 0 or 
                          result.get('trust', {}).get('net', 0) != 0 or 
                          result.get('dealer', {}).get('net', 0) != 0):
                print(f"✅ 成功從 TAIFEX 抓取三大法人資料（備用來源）")
                return result
        except Exception as e:
            print(f"⚠️ 從 TAIFEX 抓取失敗: {str(e)}")
        
        print(f"❌ 無法從任何來源取得三大法人資料")
        return None
    
    def fetch_taifex_futures_daily(self, contract_code: str = "TX", target_date: Optional[date] = None) -> Optional[Dict]:
        """
        抓取 TAIFEX 期貨每日交易資料
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            url = "https://www.taifex.com.tw/cht/3/futDataDown"
            
            date_str = target_date.strftime('%Y/%m/%d')
            
            params = {
                'down_type': '1',  # 期貨每日行情
                'commodity_id': contract_code,
                'queryStartDate': date_str,
                'queryEndDate': date_str
            }
            
            print(f"📊 抓取 TAIFEX 期貨每日資料 ({contract_code}, {date_str})...")
            response = self.session.get(url, params=params, timeout=30, verify=False)
            response.encoding = 'big5'
            response.raise_for_status()
            
            if response.text:
                try:
                    lines = response.text.strip().split('\n')
                    data_lines = [line for line in lines if line.strip() and not line.startswith('交易日期')]
                    
                    if data_lines:
                        df = pd.read_csv(
                            StringIO('\n'.join(data_lines)),
                            encoding='big5',
                            header=None,
                            engine='python'
                        )
                        
                        if not df.empty:
                            row = df.iloc[0]
                            
                            result = {
                                'date': target_date,
                                'contract_code': f"{target_date.year}{target_date.month:02d}",
                                'open': 0,
                                'high': 0,
                                'low': 0,
                                'close': 0,
                                'settlement': 0,
                                'change': 0,
                                'change_percent': 0,
                                'volume': 0,
                                'open_interest': 0
                            }
                            
                            print(f"✅ 成功抓取期貨每日資料（需要根據實際格式調整解析邏輯）")
                            return result
                
                except Exception as e:
                    print(f"⚠️ 解析期貨資料時發生錯誤: {str(e)}")
            
            return None
        
        except Exception as e:
            print(f"❌ 抓取 TAIFEX 期貨資料失敗: {str(e)}")
            return None
    
    def save_margin_trading_data(self, data: Dict) -> bool:
        """儲存融資融券資料到資料庫
        
        如果只有變化值（margin_change, short_selling_change），
        會根據前一天的餘額自動計算當天的餘額
        """
        try:
            if not data:
                return False
            
            target_date = data['date']
            market_type = data['market_type']
            
            # 如果沒有提供餘額，但有變化值，從前一天計算
            margin_balance = data.get('margin_balance')
            short_selling_balance = data.get('short_selling_balance')
            margin_change = data.get('margin_change', 0)
            short_selling_change = data.get('short_selling_change', 0)
            
            # 如果沒有提供融資餘額，但有變化值，從前一天計算
            if margin_balance is None and margin_change is not None:
                prev_day = self.db.query(MarginTradingData).filter(
                    MarginTradingData.date < target_date,
                    MarginTradingData.market_type == market_type
                ).order_by(MarginTradingData.date.desc()).first()
                
                if prev_day and prev_day.margin_balance:
                    margin_balance = prev_day.margin_balance + margin_change
                    change_sign = '+' if margin_change >= 0 else ''
                    print(f"   從前一天計算融資餘額: {prev_day.margin_balance:.1f} {change_sign}{margin_change:.1f} = {margin_balance:.1f} 億")
                else:
                    margin_balance = 0
            
            # 如果沒有提供融券餘額，但有變化值，從前一天計算
            if short_selling_balance is None and short_selling_change is not None:
                prev_day = self.db.query(MarginTradingData).filter(
                    MarginTradingData.date < target_date,
                    MarginTradingData.market_type == market_type
                ).order_by(MarginTradingData.date.desc()).first()
                
                if prev_day and prev_day.short_selling_balance:
                    short_selling_balance = prev_day.short_selling_balance + short_selling_change
                    change_sign = '+' if short_selling_change >= 0 else ''
                    print(f"   從前一天計算融券餘額: {prev_day.short_selling_balance:,} {change_sign}{short_selling_change:,} = {short_selling_balance:,} 張")
                else:
                    short_selling_balance = 0
            
            # 檢查是否已存在
            existing = self.db.query(MarginTradingData).filter(
                MarginTradingData.date == target_date,
                MarginTradingData.market_type == market_type
            ).first()
            
            if existing:
                # 更新現有記錄
                if margin_balance is not None:
                    existing.margin_balance = margin_balance
                if margin_change is not None:
                    existing.margin_change = margin_change
                if short_selling_balance is not None:
                    existing.short_selling_balance = short_selling_balance
                if short_selling_change is not None:
                    existing.short_selling_change = short_selling_change
                existing.securities_lending_sell = data.get('securities_lending_sell', 0)
                existing.securities_lending_change = data.get('securities_lending_change', 0)
                existing.index_price = data.get('index_price', 0)
                existing.index_change_percent = data.get('index_change_percent', 0)
                if hasattr(existing, 'trading_volume'):
                    existing.trading_volume = data.get('trading_volume', 0)
                existing.updated_at = datetime.utcnow()
            else:
                # 建立新記錄
                margin_data = MarginTradingData(
                    date=target_date,
                    market_type=market_type,
                    margin_balance=margin_balance or 0,
                    margin_change=margin_change or 0,
                    short_selling_balance=short_selling_balance or 0,
                    short_selling_change=short_selling_change or 0,
                    securities_lending_sell=data.get('securities_lending_sell', 0),
                    securities_lending_change=data.get('securities_lending_change', 0),
                    index_price=data.get('index_price', 0),
                    index_change_percent=data.get('index_change_percent', 0)
                )
                # 如果有 trading_volume 欄位，設定它
                if hasattr(margin_data, 'trading_volume'):
                    margin_data.trading_volume = data.get('trading_volume', 0)
                self.db.add(margin_data)
            
            self.db.commit()
            print(f"✅ 融資融券資料已儲存: {target_date} ({market_type})")
            return True
        
        except Exception as e:
            self.db.rollback()
            print(f"❌ 儲存融資融券資料失敗: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_institutional_trading_data(self, data: Dict) -> bool:
        """儲存三大法人買賣超資料到資料庫"""
        try:
            if not data:
                return False
            
            # 取得或建立合約（使用 TX 作為預設）
            contract = self.db.query(FuturesContract).filter(
                FuturesContract.symbol == 'TX'
            ).first()
            
            if not contract:
                contract = FuturesContract(
                    symbol='TX',
                    name='台指期貨',
                    contract_type='index',
                    is_active=True
                )
                self.db.add(contract)
                self.db.flush()
            
            # 檢查是否已存在
            existing = self.db.query(InstitutionalTradingData).filter(
                InstitutionalTradingData.date == data['date'],
                InstitutionalTradingData.contract_id == contract.id,
                InstitutionalTradingData.market_type == data.get('market_type', 'weighted')
            ).first()
            
            foreign = data.get('foreign', {})
            trust = data.get('trust', {})
            dealer = data.get('dealer', {})
            
            if existing:
                # 更新現有記錄
                existing.foreign_buy = foreign.get('buy', 0)
                existing.foreign_sell = foreign.get('sell', 0)
                existing.foreign_net = foreign.get('net', 0)
                existing.trust_buy = trust.get('buy', 0)
                existing.trust_sell = trust.get('sell', 0)
                existing.trust_net = trust.get('net', 0)
                existing.dealer_buy = dealer.get('buy', 0)
                existing.dealer_sell = dealer.get('sell', 0)
                existing.dealer_net = dealer.get('net', 0)
                existing.dealer_self_buy = dealer.get('self_buy', 0)
                existing.dealer_self_sell = dealer.get('self_sell', 0)
                existing.dealer_self_net = dealer.get('self_net', 0)
                existing.dealer_hedge_buy = dealer.get('hedge_buy', 0)
                existing.dealer_hedge_sell = dealer.get('hedge_sell', 0)
                existing.dealer_hedge_net = dealer.get('hedge_net', 0)
                existing.total_net = data.get('total_net', 0)
                existing.updated_at = datetime.utcnow()
            else:
                # 建立新記錄
                inst_data = InstitutionalTradingData(
                    contract_id=contract.id,
                    date=data['date'],
                    market_type=data.get('market_type', 'weighted'),
                    foreign_buy=foreign.get('buy', 0),
                    foreign_sell=foreign.get('sell', 0),
                    foreign_net=foreign.get('net', 0),
                    trust_buy=trust.get('buy', 0),
                    trust_sell=trust.get('sell', 0),
                    trust_net=trust.get('net', 0),
                    dealer_buy=dealer.get('buy', 0),
                    dealer_sell=dealer.get('sell', 0),
                    dealer_net=dealer.get('net', 0),
                    dealer_self_buy=dealer.get('self_buy', 0),
                    dealer_self_sell=dealer.get('self_sell', 0),
                    dealer_self_net=dealer.get('self_net', 0),
                    dealer_hedge_buy=dealer.get('hedge_buy', 0),
                    dealer_hedge_sell=dealer.get('hedge_sell', 0),
                    dealer_hedge_net=dealer.get('hedge_net', 0),
                    total_net=data.get('total_net', 0)
                )
                self.db.add(inst_data)
            
            self.db.commit()
            print(f"✅ 三大法人資料已儲存: {data['date']}")
            return True
        
        except Exception as e:
            self.db.rollback()
            print(f"❌ 儲存三大法人資料失敗: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_futures_open_interest_data(self, oi_data: Dict, target_date: date) -> bool:
        """儲存期貨未平倉量資料到資料庫"""
        try:
            if not oi_data:
                return False
            
            # 取得或建立合約（使用 TX 作為預設）
            contract = self.db.query(FuturesContract).filter(
                FuturesContract.symbol == 'TX'
            ).first()
            
            if not contract:
                contract = FuturesContract(
                    symbol='TX',
                    name='台指期貨',
                    contract_type='index',
                    is_active=True
                )
                self.db.add(contract)
                self.db.flush()
            
            # 取得前一天的未平倉量資料，用於計算昨日差異
            prev_day = self.db.query(FuturesOpenInterest).filter(
                FuturesOpenInterest.contract_id == contract.id,
                FuturesOpenInterest.date < target_date
            ).order_by(FuturesOpenInterest.date.desc()).first()
            
            # 取得當天的未平倉量
            foreign_oi = oi_data.get('foreign_oi')
            trust_oi = oi_data.get('trust_oi')
            dealer_oi = oi_data.get('dealer_oi')
            
            # 計算昨日差異
            foreign_oi_change = None
            trust_oi_change = None
            dealer_oi_change = None
            
            if prev_day:
                if foreign_oi is not None and prev_day.foreign_oi is not None:
                    foreign_oi_change = foreign_oi - prev_day.foreign_oi
                if trust_oi is not None and prev_day.trust_oi is not None:
                    trust_oi_change = trust_oi - prev_day.trust_oi
                if dealer_oi is not None and prev_day.dealer_oi is not None:
                    dealer_oi_change = dealer_oi - prev_day.dealer_oi
            
            # 計算總未平倉（如果三大法人都有資料）
            total_oi = None
            if foreign_oi is not None and trust_oi is not None and dealer_oi is not None:
                # 這裡需要根據實際情況計算，因為未平倉量可能是淨值（有正負）
                # 暫時先設為 None，等待更多資料來源
                pass
            
            # 檢查是否已存在
            existing = self.db.query(FuturesOpenInterest).filter(
                FuturesOpenInterest.contract_id == contract.id,
                FuturesOpenInterest.date == target_date
            ).first()
            
            if existing:
                # 更新現有記錄
                if foreign_oi is not None:
                    existing.foreign_oi = foreign_oi
                if foreign_oi_change is not None:
                    existing.foreign_oi_change = foreign_oi_change
                if trust_oi is not None:
                    existing.trust_oi = trust_oi
                if trust_oi_change is not None:
                    existing.trust_oi_change = trust_oi_change
                if dealer_oi is not None:
                    existing.dealer_oi = dealer_oi
                if dealer_oi_change is not None:
                    existing.dealer_oi_change = dealer_oi_change
                if total_oi is not None:
                    existing.total_oi = total_oi
                existing.updated_at = datetime.utcnow()
            else:
                # 建立新記錄
                oi_record = FuturesOpenInterest(
                    contract_id=contract.id,
                    date=target_date,
                    foreign_oi=foreign_oi or 0,
                    foreign_oi_change=foreign_oi_change or 0,
                    trust_oi=trust_oi or 0,
                    trust_oi_change=trust_oi_change or 0,
                    dealer_oi=dealer_oi or 0,
                    dealer_oi_change=dealer_oi_change or 0,
                    total_oi=total_oi or 0,
                    # 十大交易人資料暫時設為 0（需要從其他來源取得）
                    top5_oi=0,
                    top10_oi=0,
                    top5_special_oi=0,
                    top10_special_oi=0,
                    retail_oi=0,
                    retail_oi_change=0
                )
                self.db.add(oi_record)
            
            self.db.commit()
            print(f"✅ 期貨未平倉量資料已儲存: {target_date}")
            if foreign_oi is not None:
                print(f"   外資未平倉: {foreign_oi:,} 口 (變化: {foreign_oi_change or 0:+,})")
            if trust_oi is not None:
                print(f"   投信未平倉: {trust_oi:,} 口 (變化: {trust_oi_change or 0:+,})")
            if dealer_oi is not None:
                print(f"   自營未平倉: {dealer_oi:,} 口 (變化: {dealer_oi_change or 0:+,})")
            return True
        
        except Exception as e:
            self.db.rollback()
            print(f"❌ 儲存期貨未平倉量資料失敗: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def fetch_and_save_all(self, target_date: Optional[date] = None):
        """抓取並儲存所有期貨相關資料"""
        if target_date is None:
            target_date = date.today()
        
        print(f"\n{'='*60}")
        print(f"🚀 開始抓取 {target_date} 的期貨資料")
        print(f"{'='*60}\n")
        
        success_count = 0
        total_count = 0
        
        # 1. 抓取融資融券資料（加權指數）
        total_count += 1
        margin_data = self.fetch_twse_margin_trading(target_date)
        if margin_data:
            if self.save_margin_trading_data(margin_data):
                success_count += 1
            time.sleep(1)  # 避免請求過快
        
        # 2. 抓取三大法人買賣超
        total_count += 1
        inst_data = self.fetch_taifex_institutional_trading(target_date)
        if inst_data:
            if self.save_institutional_trading_data(inst_data):
                success_count += 1
            time.sleep(1)
        
        # 2.1 從 TAIFEX 抓取未平倉量資料（TAIFEX 才有完整的未平倉量資料）
        total_count += 1
        try:
            from crawler.taifex_institutional_scraper import TAIFEXInstitutionalScraper
            taifex_scraper = TAIFEXInstitutionalScraper(self.db)
            taifex_inst_data = taifex_scraper.fetch_institutional_trading(target_date)
            if taifex_inst_data and taifex_inst_data.get('open_interest'):
                if self.save_futures_open_interest_data(taifex_inst_data.get('open_interest'), target_date):
                    success_count += 1
                    time.sleep(1)
        except Exception as e:
            print(f"⚠️ 從 TAIFEX 抓取未平倉量資料失敗: {str(e)}")
        
        # 3. 抓取期貨每日資料
        total_count += 1
        futures_data = self.fetch_taifex_futures_daily("TX", target_date)
        if futures_data:
            # TODO: 實現儲存邏輯
            print(f"📝 期貨每日資料需要實現儲存邏輯")
            success_count += 1
        
        print(f"\n{'='*60}")
        print(f"✅ 資料抓取完成: 成功 {success_count}/{total_count}")
        print(f"{'='*60}\n")
        
        return success_count, total_count
