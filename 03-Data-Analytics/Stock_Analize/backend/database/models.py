"""
資料庫模型定義
"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, BigInteger, Boolean, ForeignKey, Text, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Stock(Base):
    """股票基本資料表"""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    market = Column(String(10), nullable=False, index=True)  # 'TW', 'US', etc.
    name = Column(String(100), nullable=False)
    full_name = Column(String(200))
    industry = Column(String(50))
    sector = Column(String(50))
    website = Column(String(255))
    description = Column(Text)
    currency = Column(String(10), default='TWD')
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    prices = relationship("StockPrice", back_populates="stock", cascade="all, delete-orphan")
    indicators = relationship("TechnicalIndicator", back_populates="stock", cascade="all, delete-orphan")
    news = relationship("StockNews", back_populates="stock", cascade="all, delete-orphan")

class StockPrice(Base):
    """股票價格資料表"""
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, default=0)
    turnover = Column(Float)  # 成交額
    change_amount = Column(Float)  # 漲跌金額
    change_percent = Column(Float)  # 漲跌幅百分比
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    stock = relationship("Stock", back_populates="prices")
    
    # 唯一約束
    __table_args__ = (UniqueConstraint('stock_id', 'date', name='uq_stock_price'),)

class TechnicalIndicator(Base):
    """技術指標表"""
    __tablename__ = "technical_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    indicator_type = Column(String(20), nullable=False, index=True)  # 'MA', 'RSI', 'MACD', etc.
    indicator_name = Column(String(50), nullable=False)  # 'MA5', 'RSI14', etc.
    value = Column(Float, nullable=False)
    period = Column(Integer)  # 計算週期
    extra_data = Column(JSON)  # 額外資料（如 MACD 的 signal, hist）
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 關聯
    stock = relationship("Stock", back_populates="indicators")
    
    # 唯一約束
    __table_args__ = (UniqueConstraint('stock_id', 'date', 'indicator_type', 'indicator_name', name='uq_technical_indicator'),)

class StockNews(Base):
    """股票新聞表"""
    __tablename__ = "stock_news"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    source = Column(String(100))
    url = Column(String(500))
    published_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 關聯
    stock = relationship("Stock", back_populates="news")

class DataSyncLog(Base):
    """資料同步日誌表"""
    __tablename__ = "data_sync_log"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), index=True)
    sync_type = Column(String(20), nullable=False)  # 'price', 'indicator', etc.
    status = Column(String(20), nullable=False, index=True)  # 'success', 'failed', 'partial'
    records_count = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

