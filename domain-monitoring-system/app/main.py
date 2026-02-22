"""FastAPI main application"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import logging
import os

from app.config import settings
from app.database import get_db, init_db
from app.models import Domain, Nameserver, Alert, MonitoringEvent
from app.schemas import (
    DomainCreate, DomainUpdate, DomainResponse,
    NameserverCreate, NameserverResponse,
    AlertResponse, MonitoringEventResponse,
    DNSCheckRequest, DNSCheckResponse
)
from app.dns_checker import DNSChecker
from app.decision_engine import AlertDecisionEngine
from app.notifier import SlackNotifier

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Domain Monitoring System",
    description="全方位網域資產監控與交叉驗證系統",
    version="1.0.0"
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Application started successfully")


@app.get("/")
async def root():
    """Redirect to dashboard"""
    return FileResponse(os.path.join(static_dir, "dashboard.html"))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Domain Monitoring System",
        "version": "1.0.0"
    }


# ==================== Domain Management APIs ====================

@app.post("/api/domains", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def create_domain(domain_data: DomainCreate, db: Session = Depends(get_db)):
    """建立新的網域監控"""
    # Check if domain already exists
    existing = db.query(Domain).filter(Domain.domain == domain_data.domain).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Domain {domain_data.domain} already exists"
        )
    
    # Create new domain
    domain = Domain(
        domain=domain_data.domain,
        expected_ips=domain_data.expected_ips,
        expected_ns=domain_data.expected_ns,
        keyword=domain_data.keyword,
        check_interval=domain_data.check_interval
    )
    
    db.add(domain)
    db.commit()
    db.refresh(domain)
    
    logger.info(f"Created domain monitoring for: {domain.domain}")
    return domain


@app.get("/api/domains", response_model=List[DomainResponse])
async def list_domains(skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    """列出所有監控的網域 (預設最多 1000 筆)"""
    domains = db.query(Domain).offset(skip).limit(limit).all()
    return domains


@app.get("/api/domains/{domain_id}", response_model=DomainResponse)
async def get_domain(domain_id: int, db: Session = Depends(get_db)):
    """取得特定網域的詳細資訊"""
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain


@app.put("/api/domains/{domain_id}", response_model=DomainResponse)
async def update_domain(domain_id: int, domain_data: DomainUpdate, db: Session = Depends(get_db)):
    """更新網域監控設定"""
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    # Update fields
    update_data = domain_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(domain, field, value)
    
    db.commit()
    db.refresh(domain)
    
    logger.info(f"Updated domain: {domain.domain}")
    return domain


@app.delete("/api/domains/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain(domain_id: int, db: Session = Depends(get_db)):
    """刪除網域監控"""
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    db.delete(domain)
    db.commit()
    
    logger.info(f"Deleted domain: {domain.domain}")
    return None


# ==================== Nameserver Management APIs ====================

@app.post("/api/nameservers", response_model=NameserverResponse, status_code=status.HTTP_201_CREATED)
async def create_nameserver(ns_data: NameserverCreate, db: Session = Depends(get_db)):
    """新增 ISP DNS 伺服器"""
    # Check if already exists
    existing = db.query(Nameserver).filter(Nameserver.dns_server == ns_data.dns_server).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nameserver {ns_data.dns_server} already exists"
        )
    
    nameserver = Nameserver(
        country_code=ns_data.country_code.upper(),
        isp_name=ns_data.isp_name,
        dns_server=ns_data.dns_server
    )
    
    db.add(nameserver)
    db.commit()
    db.refresh(nameserver)
    
    logger.info(f"Added nameserver: {nameserver.dns_server} ({nameserver.isp_name})")
    return nameserver


@app.get("/api/nameservers", response_model=List[NameserverResponse])
async def list_nameservers(country_code: str = None, db: Session = Depends(get_db)):
    """列出所有 DNS 伺服器"""
    query = db.query(Nameserver)
    if country_code:
        query = query.filter(Nameserver.country_code == country_code.upper())
    
    nameservers = query.all()
    return nameservers


# ==================== Monitoring & Alerts APIs ====================

@app.post("/api/check/dns", response_model=DNSCheckResponse)
async def manual_dns_check(check_request: DNSCheckRequest, db: Session = Depends(get_db)):
    """手動觸發 DNS 檢查"""
    domain = db.query(Domain).filter(Domain.domain == check_request.domain).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found in monitoring list")
    
    # Get nameservers
    if check_request.nameservers:
        nameservers = check_request.nameservers
    else:
        ns_list = db.query(Nameserver).filter(Nameserver.is_healthy == True).all()
        nameservers = [ns.dns_server for ns in ns_list]
    
    # Perform DNS check
    checker = DNSChecker()
    result = await checker.check_domain_multi_ns(
        domain=domain.domain,
        nameservers=nameservers,
        expected_ips=domain.expected_ips
    )
    
    # Save event
    event = MonitoringEvent(
        domain_id=domain.id,
        event_type='dns_check',
        status='ok' if result['success_rate'] > 0.8 else 'warning',
        details=result
    )
    db.add(event)
    db.commit()
    
    return DNSCheckResponse(
        domain=domain.domain,
        status='success',
        results=result,
        timestamp=datetime.utcnow()
    )


@app.get("/api/alerts", response_model=List[AlertResponse])
async def list_alerts(
    domain_id: int = None,
    is_resolved: bool = None,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """列出告警 (包含域名資訊,預設最多 1000 筆)"""
    query = db.query(Alert)
    
    if domain_id:
        query = query.filter(Alert.domain_id == domain_id)
    if is_resolved is not None:
        query = query.filter(Alert.is_resolved == is_resolved)
    
    alerts = query.order_by(Alert.last_seen.desc()).offset(skip).limit(limit).all()
    
    # 將告警轉換為字典並加入域名資訊
    result = []
    for alert in alerts:
        alert_dict = {
            "id": alert.id,
            "domain_id": alert.domain_id,
            "domain_name": alert.domain.domain if alert.domain else "Unknown",
            "alert_level": alert.alert_level,
            "root_cause": alert.root_cause,
            "evidence": alert.evidence,
            "is_resolved": alert.is_resolved,
            "first_seen": alert.first_seen,
            "last_seen": alert.last_seen,
            "notified_at": alert.notified_at,
            "resolved_at": alert.resolved_at
        }
        result.append(alert_dict)
    
    return result


@app.get("/api/events", response_model=List[MonitoringEventResponse])
async def list_events(
    domain_id: int = None,
    event_type: str = None,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """列出監控事件 (預設最多 1000 筆)"""
    query = db.query(MonitoringEvent)
    
    if domain_id:
        query = query.filter(MonitoringEvent.domain_id == domain_id)
    if event_type:
        query = query.filter(MonitoringEvent.event_type == event_type)
    
    events = query.order_by(MonitoringEvent.timestamp.desc()).offset(skip).limit(limit).all()
    return events


# ==================== Webhook Endpoints ====================

@app.post("/webhook/uptimerobot")
async def uptimerobot_webhook(payload: dict, db: Session = Depends(get_db)):
    """接收 UptimeRobot 的 Webhook"""
    logger.info(f"Received UptimeRobot webhook: {payload}")
    
    # Extract domain from monitor name
    monitor_name = payload.get('monitorFriendlyName', '')
    alert_type = payload.get('alertType')  # 1=down, 2=up
    
    # TODO: Implement cross-validation logic
    # 1. Extract domain from monitor name
    # 2. Trigger DNS checks
    # 3. Run decision engine
    # 4. Send alerts if needed
    
    return {"status": "received", "message": "Webhook processed"}


from datetime import datetime

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

