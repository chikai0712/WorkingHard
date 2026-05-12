"""Pydantic schemas for API requests and responses"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime


class DomainCreate(BaseModel):
    """建立網域監控的請求 Schema"""
    domain: str = Field(..., description="網域名稱", example="example.com")
    expected_ips: List[str] = Field(..., description="預期的 IP 白名單", example=["1.2.3.4", "5.6.7.8"])
    expected_ns: List[str] = Field(..., description="預期的 NS 記錄", example=["ns1.example.com", "ns2.example.com"])
    keyword: Optional[str] = Field(None, description="網頁關鍵字監控", example="Welcome")
    check_interval: int = Field(300, description="檢查間隔(秒)", ge=60, le=3600)
    
    @validator('domain')
    def validate_domain(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Domain must be at least 3 characters')
        return v.lower()


class DomainUpdate(BaseModel):
    """更新網域監控的請求 Schema"""
    expected_ips: Optional[List[str]] = None
    expected_ns: Optional[List[str]] = None
    keyword: Optional[str] = None
    check_interval: Optional[int] = Field(None, ge=60, le=3600)
    is_active: Optional[bool] = None


class DomainResponse(BaseModel):
    """網域監控的回應 Schema"""
    id: int
    domain: str
    expected_ips: List[str]
    expected_ns: List[str]
    keyword: Optional[str]
    check_interval: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class NameserverCreate(BaseModel):
    """建立 DNS 伺服器的請求 Schema"""
    country_code: str = Field(..., max_length=2, description="國家代碼", example="TW")
    isp_name: str = Field(..., description="ISP 名稱", example="中華電信")
    dns_server: str = Field(..., description="DNS 伺服器 IP", example="168.95.1.1")


class NameserverResponse(BaseModel):
    """DNS 伺服器的回應 Schema"""
    id: int
    country_code: str
    isp_name: str
    dns_server: str
    is_healthy: bool
    last_check: Optional[datetime]
    response_time_ms: Optional[int]
    
    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    """告警的回應 Schema"""
    id: int
    domain_id: int
    domain_name: Optional[str] = None
    alert_level: str
    root_cause: str
    evidence: dict
    is_resolved: bool
    first_seen: datetime
    last_seen: datetime
    notified_at: Optional[datetime]
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class MonitoringEventResponse(BaseModel):
    """監控事件的回應 Schema"""
    id: int
    domain_id: int
    event_type: str
    status: str
    details: dict
    timestamp: datetime
    
    class Config:
        from_attributes = True


class DNSCheckRequest(BaseModel):
    """手動觸發 DNS 檢查的請求"""
    domain: str = Field(..., description="要檢查的網域")
    nameservers: Optional[List[str]] = Field(None, description="指定的 DNS 伺服器列表")


class DNSCheckResponse(BaseModel):
    """DNS 檢查結果"""
    domain: str
    status: str
    results: dict
    timestamp: datetime

