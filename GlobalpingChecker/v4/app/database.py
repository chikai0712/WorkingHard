"""
GlobalpingChecker V4 - Database Models & Connection
PostgreSQL with SQLAlchemy
"""
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, 
    ForeignKey, Text, Float, Boolean, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from enum import Enum

from .config import get_settings

settings = get_settings()

# Database Engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DomainStatus(str, Enum):
    """域名檢測狀態分類"""
    CLEAN = "CLEAN"           # 正常連通
    BLOCKED = "BLOCKED"       # DNS 污染/被封鎖
    TIMEOUT = "TIMEOUT"       # 完全超時
    WARNING = "WARNING"       # 服務異常（非 2xx/3xx）
    PARTIAL = "PARTIAL"       # 部分節點異常
    API_ERROR = "API_ERROR"   # API 請求失敗


class TestBatch(Base):
    """測試批次表"""
    __tablename__ = "test_batches"
    
    batch_id = Column(Integer, primary_key=True, autoincrement=True)
    test_date = Column(DateTime, default=datetime.utcnow, index=True)
    total_domains = Column(Integer, default=0)
    clean_count = Column(Integer, default=0)
    blocked_count = Column(Integer, default=0)
    timeout_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    partial_count = Column(Integer, default=0)
    api_error_count = Column(Integer, default=0)
    duration_seconds = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    is_scheduled = Column(Boolean, default=False)
    
    # Relationships
    domain_results = relationship("DomainResult", back_populates="batch", cascade="all, delete-orphan")


class DomainResult(Base):
    """域名測試結果表"""
    __tablename__ = "domain_results"
    
    result_id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey("test_batches.batch_id", ondelete="CASCADE"), index=True)
    domain = Column(String(255), nullable=False, index=True)
    overall_status = Column(String(20), nullable=False, index=True)
    test_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    batch = relationship("TestBatch", back_populates="domain_results")
    node_details = relationship("NodeDetail", back_populates="domain_result", cascade="all, delete-orphan")


class NodeDetail(Base):
    """節點測試詳情表"""
    __tablename__ = "node_details"
    
    detail_id = Column(Integer, primary_key=True, autoincrement=True)
    result_id = Column(Integer, ForeignKey("domain_results.result_id", ondelete="CASCADE"), index=True)
    
    # 節點信息
    node_isp = Column(String(100), nullable=True)
    node_asn = Column(String(20), nullable=True)
    node_city = Column(String(100), nullable=True)
    node_country = Column(String(10), default="ID")
    node_ip = Column(String(50), nullable=True)
    
    # 測試結果
    target_ip = Column(String(50), nullable=True)
    status = Column(String(20), nullable=True)
    http_code = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    domain_result = relationship("DomainResult", back_populates="node_details")


class DomainHistory(Base):
    """域名歷史狀態追蹤表（用於異常監控）"""
    __tablename__ = "domain_history"
    
    history_id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String(255), nullable=False, index=True)
    previous_status = Column(String(20), nullable=True)
    current_status = Column(String(20), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, index=True)
    batch_id = Column(Integer, ForeignKey("test_batches.batch_id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)


class SchedulerLog(Base):
    """排程執行日誌"""
    __tablename__ = "scheduler_logs"
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    run_time = Column(DateTime, default=datetime.utcnow, index=True)
    batch_id = Column(Integer, ForeignKey("test_batches.batch_id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), nullable=False)  # SUCCESS, FAILED, RUNNING
    domains_checked = Column(Integer, default=0)
    duration_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)


def init_db():
    """初始化資料庫表"""
    Base.metadata.create_all(bind=engine)
    print("✅ PostgreSQL 資料庫初始化完成")


def get_db():
    """獲取資料庫 Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
