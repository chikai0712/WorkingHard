"""
GlobalpingChecker V4.1 - Database Models
智能循環檢測系統 - 資料庫模型
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, DateTime, Float, Boolean, 
    Text, ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class DomainStatus(str, Enum):
    """域名檢測狀態"""
    CLEAN = "CLEAN"           # 正常連通
    BLOCKED = "BLOCKED"       # DNS 污染
    TIMEOUT = "TIMEOUT"       # 完全超時
    WARNING = "WARNING"       # 服務異常 (4xx/5xx)
    PARTIAL = "PARTIAL"       # 部分異常
    API_ERROR = "API_ERROR"   # API 錯誤


class DomainZone(str, Enum):
    """域名所屬區域"""
    NORMAL = "NORMAL"         # 正常區
    ABNORMAL = "ABNORMAL"     # 異常區
    PENDING = "PENDING"       # 待分類（初始狀態）


class CycleType(str, Enum):
    """循環類型"""
    ABNORMAL_CHECK = "ABNORMAL_CHECK"   # 第一循環：檢測異常區
    NORMAL_CHECK = "NORMAL_CHECK"       # 第二循環：檢測正常區


# ==================== 域名管理 ====================

class Domain(Base):
    """域名主表 - 管理域名狀態和所屬區域"""
    __tablename__ = "domains"
    
    domain_id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    zone = Column(SQLEnum(DomainZone), default=DomainZone.PENDING, nullable=False)
    current_status = Column(SQLEnum(DomainStatus), nullable=True)
    last_check_time = Column(DateTime, nullable=True)
    consecutive_normal = Column(Integer, default=0)    # 連續正常次數
    consecutive_abnormal = Column(Integer, default=0)  # 連續異常次數
    total_checks = Column(Integer, default=0)          # 總檢測次數
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    results = relationship("DomainResult", back_populates="domain_ref")
    zone_history = relationship("DomainZoneHistory", back_populates="domain_ref")
    
    __table_args__ = (
        Index('idx_domain_zone', 'zone'),
        Index('idx_domain_status', 'current_status'),
    )


class DomainZoneHistory(Base):
    """域名區域變更歷史"""
    __tablename__ = "domain_zone_history"
    
    history_id = Column(Integer, primary_key=True, autoincrement=True)
    domain_id = Column(Integer, ForeignKey("domains.domain_id"), nullable=False)
    previous_zone = Column(SQLEnum(DomainZone), nullable=True)
    new_zone = Column(SQLEnum(DomainZone), nullable=False)
    reason = Column(String(500))  # 變更原因
    changed_at = Column(DateTime, default=datetime.utcnow)
    batch_id = Column(Integer, ForeignKey("test_batches.batch_id"), nullable=True)
    
    domain_ref = relationship("Domain", back_populates="zone_history")


# ==================== 循環管理 ====================

class CheckCycle(Base):
    """檢測循環記錄"""
    __tablename__ = "check_cycles"
    
    cycle_id = Column(Integer, primary_key=True, autoincrement=True)
    cycle_type = Column(SQLEnum(CycleType), nullable=False)
    cycle_number = Column(Integer, default=1)          # 當前循環編號
    iteration = Column(Integer, default=1)             # 循環內的第幾次檢測
    max_iterations = Column(Integer, default=10)       # 最大檢測次數（第一循環）
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    total_domains = Column(Integer, default=0)
    normal_count = Column(Integer, default=0)
    abnormal_count = Column(Integer, default=0)
    
    # 關聯
    batches = relationship("TestBatch", back_populates="cycle")


class CycleSchedule(Base):
    """循環排程配置"""
    __tablename__ = "cycle_schedules"
    
    schedule_id = Column(Integer, primary_key=True, autoincrement=True)
    cycle_type = Column(SQLEnum(CycleType), nullable=False)
    start_hour = Column(Integer, nullable=False)       # 開始時間（小時，0-23）
    start_minute = Column(Integer, default=0)          # 開始時間（分鐘）
    check_interval_minutes = Column(Integer, default=90)  # 檢測間隔
    is_enabled = Column(Boolean, default=True)
    description = Column(String(255))


# ==================== 檢測結果 ====================

class TestBatch(Base):
    """測試批次"""
    __tablename__ = "test_batches"
    
    batch_id = Column(Integer, primary_key=True, autoincrement=True)
    cycle_id = Column(Integer, ForeignKey("check_cycles.cycle_id"), nullable=True)
    cycle_type = Column(SQLEnum(CycleType), nullable=True)
    iteration = Column(Integer, nullable=True)         # 循環內第幾次
    test_date = Column(DateTime, default=datetime.utcnow)
    total_domains = Column(Integer, default=0)
    clean_count = Column(Integer, default=0)
    blocked_count = Column(Integer, default=0)
    timeout_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    partial_count = Column(Integer, default=0)
    api_error_count = Column(Integer, default=0)
    duration_seconds = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    
    # 區域變更統計
    moved_to_normal = Column(Integer, default=0)       # 移到正常區的數量
    moved_to_abnormal = Column(Integer, default=0)     # 移到異常區的數量
    
    # 關聯
    cycle = relationship("CheckCycle", back_populates="batches")
    results = relationship("DomainResult", back_populates="batch")


class DomainResult(Base):
    """域名檢測結果"""
    __tablename__ = "domain_results"
    
    result_id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey("test_batches.batch_id"), nullable=False)
    domain_id = Column(Integer, ForeignKey("domains.domain_id"), nullable=False)
    domain = Column(String(255), nullable=False, index=True)
    overall_status = Column(SQLEnum(DomainStatus), nullable=False)
    previous_zone = Column(SQLEnum(DomainZone), nullable=True)
    new_zone = Column(SQLEnum(DomainZone), nullable=True)
    zone_changed = Column(Boolean, default=False)
    test_date = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text, nullable=True)        # 錯誤訊息分析
    
    # 關聯
    batch = relationship("TestBatch", back_populates="results")
    domain_ref = relationship("Domain", back_populates="results")
    nodes = relationship("NodeDetail", back_populates="result")
    
    __table_args__ = (
        Index('idx_result_batch', 'batch_id'),
        Index('idx_result_domain', 'domain'),
    )


class NodeDetail(Base):
    """節點檢測詳情"""
    __tablename__ = "node_details"
    
    node_id = Column(Integer, primary_key=True, autoincrement=True)
    result_id = Column(Integer, ForeignKey("domain_results.result_id"), nullable=False)
    node_isp = Column(String(255))
    node_asn = Column(String(50))
    node_city = Column(String(100))
    node_country = Column(String(10), default="ID")
    node_ip = Column(String(50))
    target_ip = Column(String(50))
    status = Column(SQLEnum(DomainStatus))
    http_code = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    
    result = relationship("DomainResult", back_populates="nodes")


# ==================== 系統日誌 ====================

class SystemLog(Base):
    """系統運行日誌"""
    __tablename__ = "system_logs"
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    log_time = Column(DateTime, default=datetime.utcnow)
    log_type = Column(String(50))  # CYCLE_SWITCH, CHECK_START, CHECK_END, ERROR
    message = Column(Text)
    details = Column(Text, nullable=True)  # JSON 格式的詳細信息
