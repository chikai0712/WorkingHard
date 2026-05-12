"""
GlobalpingChecker V5 - Database Models

變更自 V4.1：
- NodePool 表新增 country_name, is_top_isp 欄位
- Domain 表新增 country 欄位（支援多國家）
- Alert 表（V5 新增）：記錄 Telegram 告警歷史
- DomainResult 新增 check_duration_ms 欄位
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


# ==================== Enums ====================

class DomainStatus(str, Enum):
    CLEAN     = "CLEAN"
    BLOCKED   = "BLOCKED"
    TIMEOUT   = "TIMEOUT"
    WARNING   = "WARNING"
    PARTIAL   = "PARTIAL"
    API_ERROR = "API_ERROR"


class DomainZone(str, Enum):
    NORMAL   = "NORMAL"
    ABNORMAL = "ABNORMAL"
    PENDING  = "PENDING"


class CycleType(str, Enum):
    ABNORMAL_CHECK = "ABNORMAL_CHECK"
    NORMAL_CHECK   = "NORMAL_CHECK"


class AlertType(str, Enum):
    ZONE_CHANGE      = "ZONE_CHANGE"
    API_ERROR        = "API_ERROR"
    CYCLE_COMPLETE   = "CYCLE_COMPLETE"
    QUOTA_WARNING    = "QUOTA_WARNING"


# ==================== 域名管理 ====================

class Domain(Base):
    """域名主表（V5：新增 country 欄位）"""
    __tablename__ = "domains"

    domain_id            = Column(Integer, primary_key=True, autoincrement=True)
    domain               = Column(String(255), unique=True, nullable=False, index=True)
    zone                 = Column(SQLEnum(DomainZone), default=DomainZone.PENDING, nullable=False)
    current_status       = Column(SQLEnum(DomainStatus), nullable=True)
    last_check_time      = Column(DateTime, nullable=True)
    consecutive_normal   = Column(Integer, default=0)
    consecutive_abnormal = Column(Integer, default=0)
    total_checks         = Column(Integer, default=0)
    # V5 新增：追蹤主要檢測國家
    primary_country      = Column(String(10), default="ID")
    created_at           = Column(DateTime, default=datetime.utcnow)
    updated_at           = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    results      = relationship("DomainResult", back_populates="domain_ref")
    zone_history = relationship("DomainZoneHistory", back_populates="domain_ref")

    __table_args__ = (
        Index('idx_domain_zone', 'zone'),
        Index('idx_domain_status', 'current_status'),
    )


class DomainZoneHistory(Base):
    __tablename__ = "domain_zone_history"

    history_id    = Column(Integer, primary_key=True, autoincrement=True)
    domain_id     = Column(Integer, ForeignKey("domains.domain_id"), nullable=False)
    previous_zone = Column(SQLEnum(DomainZone), nullable=True)
    new_zone      = Column(SQLEnum(DomainZone), nullable=False)
    reason        = Column(String(500))
    changed_at    = Column(DateTime, default=datetime.utcnow)
    batch_id      = Column(Integer, ForeignKey("test_batches.batch_id"), nullable=True)

    domain_ref = relationship("Domain", back_populates="zone_history")


# ==================== 循環管理 ====================

class CheckCycle(Base):
    __tablename__ = "check_cycles"

    cycle_id       = Column(Integer, primary_key=True, autoincrement=True)
    cycle_type     = Column(SQLEnum(CycleType), nullable=False)
    cycle_number   = Column(Integer, default=1)
    iteration      = Column(Integer, default=1)
    max_iterations = Column(Integer, default=10)
    started_at     = Column(DateTime, default=datetime.utcnow)
    ended_at       = Column(DateTime, nullable=True)
    is_active      = Column(Boolean, default=True)
    total_domains  = Column(Integer, default=0)
    normal_count   = Column(Integer, default=0)
    abnormal_count = Column(Integer, default=0)

    batches = relationship("TestBatch", back_populates="cycle")


class CycleSchedule(Base):
    """循環排程配置"""
    __tablename__ = "cycle_schedules"

    schedule_id              = Column(Integer, primary_key=True, autoincrement=True)
    cycle_type               = Column(SQLEnum(CycleType), nullable=False)
    start_hour               = Column(Integer, nullable=False)
    start_minute             = Column(Integer, default=0)
    check_interval_minutes   = Column(Integer, default=90)
    is_enabled               = Column(Boolean, default=True)
    description              = Column(String(255))


# ==================== 檢測結果 ====================

class TestBatch(Base):
    __tablename__ = "test_batches"

    batch_id        = Column(Integer, primary_key=True, autoincrement=True)
    cycle_id        = Column(Integer, ForeignKey("check_cycles.cycle_id"), nullable=True)
    cycle_type      = Column(SQLEnum(CycleType), nullable=True)
    iteration       = Column(Integer, nullable=True)
    test_date       = Column(DateTime, default=datetime.utcnow)
    total_domains   = Column(Integer, default=0)
    clean_count     = Column(Integer, default=0)
    blocked_count   = Column(Integer, default=0)
    timeout_count   = Column(Integer, default=0)
    warning_count   = Column(Integer, default=0)
    partial_count   = Column(Integer, default=0)
    api_error_count = Column(Integer, default=0)
    duration_seconds = Column(Float, nullable=True)
    notes           = Column(Text, nullable=True)
    moved_to_normal   = Column(Integer, default=0)
    moved_to_abnormal = Column(Integer, default=0)
    # V5 新增：記錄本批次消耗的 API 額度
    api_calls_used  = Column(Integer, default=0)

    cycle   = relationship("CheckCycle", back_populates="batches")
    results = relationship("DomainResult", back_populates="batch")


class DomainResult(Base):
    __tablename__ = "domain_results"

    result_id      = Column(Integer, primary_key=True, autoincrement=True)
    batch_id       = Column(Integer, ForeignKey("test_batches.batch_id"), nullable=False)
    domain_id      = Column(Integer, ForeignKey("domains.domain_id"), nullable=False)
    domain         = Column(String(255), nullable=False, index=True)
    overall_status = Column(SQLEnum(DomainStatus), nullable=False)
    previous_zone  = Column(SQLEnum(DomainZone), nullable=True)
    new_zone       = Column(SQLEnum(DomainZone), nullable=True)
    zone_changed   = Column(Boolean, default=False)
    test_date      = Column(DateTime, default=datetime.utcnow)
    error_message  = Column(Text, nullable=True)
    # V5 新增：單域名完整檢測耗時
    check_duration_ms = Column(Integer, nullable=True)

    batch      = relationship("TestBatch", back_populates="results")
    domain_ref = relationship("Domain", back_populates="results")
    nodes      = relationship("NodeDetail", back_populates="result")

    __table_args__ = (
        Index('idx_result_batch', 'batch_id'),
        Index('idx_result_domain', 'domain'),
    )


class NodeDetail(Base):
    __tablename__ = "node_details"

    node_id          = Column(Integer, primary_key=True, autoincrement=True)
    result_id        = Column(Integer, ForeignKey("domain_results.result_id"), nullable=False)
    node_isp         = Column(String(255))
    node_asn         = Column(String(50))
    node_city        = Column(String(100))
    node_country     = Column(String(10), default="ID")
    node_ip          = Column(String(50))
    target_ip        = Column(String(50))
    status           = Column(SQLEnum(DomainStatus))
    http_code        = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    error_message    = Column(Text, nullable=True)

    result = relationship("DomainResult", back_populates="nodes")


# ==================== 節點池 ====================

class NodePool(Base):
    """已驗證的 Globalping 節點（V5：新增 is_top_isp 欄位）"""
    __tablename__ = "node_pool"

    node_id      = Column(String(100), primary_key=True)
    node_ip      = Column(String(50), nullable=False)
    country      = Column(String(10), nullable=False)
    country_name = Column(String(100))
    city         = Column(String(100))
    isp          = Column(String(255))
    asn          = Column(String(50))
    isp_rank     = Column(Integer, default=999)
    is_top_isp   = Column(Boolean, default=False)   # V5 新增
    is_active    = Column(Boolean, default=True)
    last_verified = Column(DateTime, nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_nodepool_country', 'country'),
        Index('idx_nodepool_active', 'is_active'),
    )


# ==================== 告警記錄（V5 新增）====================

class Alert(Base):
    """Telegram 告警歷史（V5 新增）"""
    __tablename__ = "alerts"

    alert_id   = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    message    = Column(Text, nullable=False)
    details    = Column(Text, nullable=True)    # JSON
    sent_ok    = Column(Boolean, default=False) # 是否成功送出
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== 系統日誌 ====================

class SystemLog(Base):
    __tablename__ = "system_logs"

    log_id   = Column(Integer, primary_key=True, autoincrement=True)
    log_time = Column(DateTime, default=datetime.utcnow)
    log_type = Column(String(50))
    message  = Column(Text)
    details  = Column(Text, nullable=True)
