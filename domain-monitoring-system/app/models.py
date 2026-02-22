"""Database models for Domain Monitoring System"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ARRAY, JSON, ForeignKey, Float
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Domain(Base):
    """監控網域主表"""
    __tablename__ = 'domains'

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    expected_ips = Column(ARRAY(INET), nullable=False)
    expected_ns = Column(ARRAY(String(255)), nullable=False)
    keyword = Column(String(500), nullable=True)
    check_interval = Column(Integer, default=300)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    events = relationship("MonitoringEvent", back_populates="domain")
    alerts = relationship("Alert", back_populates="domain")

    def __repr__(self):
        return f"<Domain(id={self.id}, domain='{self.domain}')>"


class Nameserver(Base):
    """ISP DNS 節點清單"""
    __tablename__ = 'nameservers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    country_code = Column(String(2), nullable=False, index=True)
    isp_name = Column(String(100), nullable=False)
    dns_server = Column(INET, nullable=False, unique=True)
    is_healthy = Column(Boolean, default=True)
    last_check = Column(TIMESTAMP, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return f"<Nameserver(id={self.id}, isp='{self.isp_name}', dns='{self.dns_server}')>"


class MonitoringEvent(Base):
    """監控事件日誌 (時序數據)"""
    __tablename__ = 'monitoring_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain_id = Column(Integer, ForeignKey('domains.id'), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # 'dns_check', 'uptime_check', 'whois_check'
    status = Column(String(20), nullable=False)  # 'ok', 'warning', 'critical'
    details = Column(JSONB, nullable=True)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow, index=True)

    # Relationships
    domain = relationship("Domain", back_populates="events")

    def __repr__(self):
        return f"<MonitoringEvent(id={self.id}, type='{self.event_type}', status='{self.status}')>"


class Alert(Base):
    """告警決策表 (去重用)"""
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain_id = Column(Integer, ForeignKey('domains.id'), nullable=False, index=True)
    alert_level = Column(String(10), nullable=False)  # 'P0', 'P1', 'P2'
    root_cause = Column(String(100), nullable=False)  # 'domain_hijacked', 'isp_blocked', etc.
    evidence = Column(JSONB, nullable=True)
    is_resolved = Column(Boolean, default=False)
    first_seen = Column(TIMESTAMP, default=datetime.utcnow)
    last_seen = Column(TIMESTAMP, default=datetime.utcnow)
    notified_at = Column(TIMESTAMP, nullable=True)
    resolved_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    domain = relationship("Domain", back_populates="alerts")

    def __repr__(self):
        return f"<Alert(id={self.id}, level='{self.alert_level}', cause='{self.root_cause}')>"

