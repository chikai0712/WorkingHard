"""
期貨與選擇權資料庫模型
"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, BigInteger, Boolean, ForeignKey, Text, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class FuturesContract(Base):
    """期貨合約基本資料表"""
    __tablename__ = "futures_contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)  # 例如: TX, MTX
    name = Column(String(100), nullable=False)  # 例如: 台指期貨, 小型台指期貨
    contract_type = Column(String(20), nullable=False)  # 'index', 'stock', 'commodity'
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    daily_data = relationship("FuturesDailyData", back_populates="contract", cascade="all, delete-orphan")
    institutional_data = relationship("InstitutionalTradingData", back_populates="contract", cascade="all, delete-orphan")

class FuturesDailyData(Base):
    """期貨每日交易資料表"""
    __tablename__ = "futures_daily_data"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("futures_contracts.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    contract_code = Column(String(50))  # 例如: 202512F3
    
    # 價格資料
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    settlement = Column(Float)  # 結算價
    change = Column(Float)  # 漲跌
    change_percent = Column(Float)  # 漲跌幅
    
    # 交易資料
    volume = Column(BigInteger)  # 成交量(口數)
    open_interest = Column(BigInteger)  # 未平倉量(口數)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    contract = relationship("FuturesContract", back_populates="daily_data")
    
    # 唯一約束
    __table_args__ = (UniqueConstraint('contract_id', 'date', 'contract_code', name='uq_futures_daily'),)

class InstitutionalTradingData(Base):
    """三大法人交易資料表"""
    __tablename__ = "institutional_trading_data"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("futures_contracts.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    market_type = Column(String(20))  # 'weighted', 'otc' 加權指數 or 櫃買指數
    
    # 三大法人買賣超 (億元)
    foreign_buy = Column(Float)  # 外資買進
    foreign_sell = Column(Float)  # 外資賣出
    foreign_net = Column(Float)  # 外資淨買賣超
    
    trust_buy = Column(Float)  # 投信買進
    trust_sell = Column(Float)  # 投信賣出
    trust_net = Column(Float)  # 投信淨買賣超
    
    dealer_buy = Column(Float)  # 自營商買進
    dealer_sell = Column(Float)  # 自營商賣出
    dealer_net = Column(Float)  # 自營商淨買賣超
    
    dealer_self_buy = Column(Float)  # 自營商自買
    dealer_self_sell = Column(Float)  # 自營商自賣
    dealer_self_net = Column(Float)  # 自營商自買淨額
    
    dealer_hedge_buy = Column(Float)  # 自營商避險買進
    dealer_hedge_sell = Column(Float)  # 自營商避險賣出
    dealer_hedge_net = Column(Float)  # 自營商避險淨額
    
    total_net = Column(Float)  # 三大法人合計
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    contract = relationship("FuturesContract", back_populates="institutional_data")
    
    # 唯一約束
    __table_args__ = (UniqueConstraint('contract_id', 'date', 'market_type', name='uq_institutional_trading'),)

class FuturesOpenInterest(Base):
    """期貨未平倉量資料表"""
    __tablename__ = "futures_open_interest"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("futures_contracts.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # 三大法人未平倉口數
    foreign_oi = Column(BigInteger)  # 外資未平倉
    foreign_oi_change = Column(BigInteger)  # 外資未平倉增減
    
    trust_oi = Column(BigInteger)  # 投信未平倉
    trust_oi_change = Column(BigInteger)  # 投信未平倉增減
    
    dealer_oi = Column(BigInteger)  # 自營未平倉
    dealer_oi_change = Column(BigInteger)  # 自營未平倉增減
    
    total_oi = Column(BigInteger)  # 總計未平倉
    
    # 十大交易人
    top5_oi = Column(BigInteger)  # 前五大未平倉
    top10_oi = Column(BigInteger)  # 前十大未平倉
    
    # 十大特定人
    top5_special_oi = Column(BigInteger)  # 前五大特定人未平倉
    top10_special_oi = Column(BigInteger)  # 前十大特定人未平倉
    
    # 散戶 (計算得出: 總未平倉 - 十大交易人)
    retail_oi = Column(BigInteger)  # 散戶未平倉
    retail_oi_change = Column(BigInteger)  # 散戶未平倉增減
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 唯一約束
    __table_args__ = (UniqueConstraint('contract_id', 'date', name='uq_futures_open_interest'),)

class OptionsDailyData(Base):
    """選擇權每日交易資料表"""
    __tablename__ = "options_daily_data"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("futures_contracts.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    contract_code = Column(String(50))  # 例如: 202512F3
    contract_period = Column(String(20))  # 'weekly', 'monthly' 週選擇權 or 月選擇權
    
    # 價格資料
    index_price = Column(Float)  # 指數價格
    change = Column(Float)  # 漲跌
    change_percent = Column(Float)  # 漲跌幅
    
    # 交易資料
    call_volume = Column(BigInteger)  # 買權成交量
    put_volume = Column(BigInteger)  # 賣權成交量
    total_volume = Column(BigInteger)  # 總成交量
    
    # 未平倉量
    call_oi = Column(BigInteger)  # 買權未平倉
    put_oi = Column(BigInteger)  # 賣權未平倉
    total_oi = Column(BigInteger)  # 總未平倉
    
    # P/C 比
    pc_ratio_volume = Column(Float)  # 成交量P/C比
    pc_ratio_oi = Column(Float)  # 未平倉P/C比
    
    # 三大法人交易口數淨額
    foreign_net_volume = Column(BigInteger)  # 外資淨交易口數
    trust_net_volume = Column(BigInteger)  # 投信淨交易口數
    dealer_net_volume = Column(BigInteger)  # 自營淨交易口數
    
    # 三大法人未平倉口數
    foreign_oi = Column(BigInteger)  # 外資未平倉
    foreign_oi_change = Column(BigInteger)  # 外資未平倉增減
    trust_oi = Column(BigInteger)  # 投信未平倉
    trust_oi_change = Column(BigInteger)  # 投信未平倉增減
    dealer_oi = Column(BigInteger)  # 自營未平倉
    dealer_oi_change = Column(BigInteger)  # 自營未平倉增減
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 唯一約束
    __table_args__ = (UniqueConstraint('contract_id', 'date', 'contract_code', 'contract_period', name='uq_options_daily'),)

class OptionsStrikeData(Base):
    """選擇權履約價資料表"""
    __tablename__ = "options_strike_data"
    
    id = Column(Integer, primary_key=True, index=True)
    options_daily_id = Column(Integer, ForeignKey("options_daily_data.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    strike_price = Column(Float, nullable=False)  # 履約價
    
    # 買權資料
    call_oi = Column(BigInteger)  # 買權未平倉
    call_oi_change = Column(BigInteger)  # 買權未平倉增減
    call_volume = Column(BigInteger)  # 買權成交量
    
    # 賣權資料
    put_oi = Column(BigInteger)  # 賣權未平倉
    put_oi_change = Column(BigInteger)  # 賣權未平倉增減
    put_volume = Column(BigInteger)  # 賣權成交量
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 唯一約束
    __table_args__ = (UniqueConstraint('options_daily_id', 'strike_price', name='uq_options_strike'),)

class MarginTradingData(Base):
    """融資融券餘額資料表"""
    __tablename__ = "margin_trading_data"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    market_type = Column(String(20))  # 'weighted', 'otc'
    
    # 融資資料 (億元)
    margin_balance = Column(Float)  # 融資餘額
    margin_change = Column(Float)  # 融資增減
    
    # 融券資料 (張)
    short_selling_balance = Column(BigInteger)  # 融券餘額
    short_selling_change = Column(BigInteger)  # 融券增減
    
    # 借券賣出 (張)
    securities_lending_sell = Column(BigInteger)  # 借券賣出
    securities_lending_change = Column(BigInteger)  # 借券賣出增減
    
    # 相關指數
    index_price = Column(Float)  # 加權指數或櫃買指數
    index_change_percent = Column(Float)  # 指數漲跌幅
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 唯一約束：同一日期和市場類型只能有一筆記錄
    __table_args__ = (UniqueConstraint('date', 'market_type', name='uq_margin_trading_date_market'),)

