"""FastAPI main application"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import Integer, func
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
from app.timezone_utils import local_now

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


@app.get("/api/domains/paused")
async def list_paused_domains(db: Session = Depends(get_db)):
    """列出所有暫停中的域名"""
    from datetime import datetime
    
    now = local_now()
    paused_domains = db.query(Domain).filter(
        Domain.paused_until != None,
        Domain.paused_until > now
    ).order_by(Domain.paused_until.desc()).all()
    
    result = []
    for domain in paused_domains:
        result.append({
            "id": domain.id,
            "domain": domain.domain,
            "paused_until": domain.paused_until.isoformat() if domain.paused_until else None,
            "pause_reason": domain.pause_reason,
            "is_active": domain.is_active,
            "remaining_hours": int((domain.paused_until - now).total_seconds() / 3600) if domain.paused_until else 0
        })
    
    return {
        "total": len(result),
        "domains": result
    }


@app.post("/api/domains/{domain_id}/resume")
async def resume_domain(domain_id: int, db: Session = Depends(get_db)):
    """手動恢復暫停的域名"""
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    if not domain.paused_until:
        raise HTTPException(status_code=400, detail="Domain is not paused")
    
    # 清除暫停狀態
    domain.paused_until = None
    domain.pause_reason = None
    db.commit()
    
    logger.info(f"Manually resumed domain: {domain.domain}")
    
    return {
        "status": "success",
        "message": f"Domain {domain.domain} has been resumed",
        "domain_id": domain.id
    }


@app.post("/api/domains/check-no-record")
async def check_no_record_domains(db: Session = Depends(get_db)):
    """手動檢測無 DNS 記錄的域名並暫停到明天 0:00"""
    from datetime import datetime, timedelta
    
    # 查詢所有啟用的域名（包含已暫停的，因為要重新檢測）
    now = local_now()
    domains = db.query(Domain).filter(Domain.is_active == True).all()
    
    if not domains:
        return {
            "status": "no_domains",
            "message": "沒有需要檢測的域名",
            "checked": 0,
            "paused": 0
        }
    
    # 獲取健康的 DNS 伺服器
    nameservers = db.query(Nameserver).filter(Nameserver.is_healthy == True).all()
    ns_list = [str(ns.dns_server) for ns in nameservers]
    
    if not ns_list:
        raise HTTPException(status_code=500, detail="沒有可用的 DNS 伺服器")
    
    checker = DNSChecker()
    checked_count = 0
    paused_count = 0
    paused_domains = []
    
    # 計算明天 0:00 的時間
    tomorrow = now + timedelta(days=1)
    next_midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    
    for domain in domains:
        try:
            # 執行 DNS 檢查（不檢查白名單，只看能否解析）
            result = await checker.check_domain_multi_ns(
                domain=domain.domain,
                nameservers=ns_list,
                expected_ips=None  # 不檢查白名單
            )
            
            checked_count += 1
            
            # 判斷是否完全無法解析
            resolution_rate = result.get('resolution_rate', 0)
            failed_ns = result.get('failed_nameservers', [])
            
            # 只統計真正的錯誤
            critical_failures = [
                ns for ns in failed_ns 
                if ns.get('severity') == 'error'
            ]
            
            # 檢查是否所有失敗都是因為無記錄
            all_no_record = all(
                'Could not contact DNS servers' in ns.get('error', '') or 
                'NXDOMAIN' in ns.get('error', '') or
                'timeout' in ns.get('error', '').lower()
                for ns in critical_failures
            ) if critical_failures else False
            
            # 如果解析率為 0 且所有失敗都是無記錄，則暫停到明天 0:00
            if resolution_rate == 0 and all_no_record and len(critical_failures) >= 3:
                domain.paused_until = next_midnight
                domain.pause_reason = f"無 DNS 記錄（{len(critical_failures)} 個 DNS 伺服器全部失敗）"
                
                paused_count += 1
                paused_domains.append({
                    "id": domain.id,
                    "domain": domain.domain,
                    "reason": domain.pause_reason
                })
                
                logger.warning(f"Paused domain {domain.domain} until next midnight (no DNS records)")
                
                # 記錄暫停事件
                event = MonitoringEvent(
                    domain_id=domain.id,
                    event_type='domain_paused',
                    status='warning',
                    details={
                        'reason': domain.pause_reason,
                        'paused_until': next_midnight.isoformat(),
                        'dns_check_result': result
                    }
                )
                db.add(event)
        
        except Exception as e:
            logger.error(f"Error checking domain {domain.domain}: {e}")
    
    db.commit()
    
    return {
        "status": "completed",
        "message": f"檢測完成：檢查了 {checked_count} 個域名，暫停了 {paused_count} 個",
        "checked": checked_count,
        "paused": paused_count,
        "paused_domains": paused_domains
    }


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


@app.get("/api/nameservers")
async def list_nameservers(
    country_code: str = None, 
    dns_type: str = None,
    db: Session = Depends(get_db)
):
    """列出所有 DNS 伺服器"""
    query = db.query(Nameserver)
    
    if country_code:
        query = query.filter(Nameserver.country_code == country_code.upper())
    
    if dns_type:
        query = query.filter(Nameserver.dns_type == dns_type)
    
    nameservers = query.all()
    
    # 轉換為字典格式
    result = []
    for ns in nameservers:
        result.append({
            "id": ns.id,
            "dns_server": str(ns.dns_server),
            "dns_type": ns.dns_type,
            "isp": ns.isp,
            "region": ns.region,
            "country_code": ns.country_code,
            "is_healthy": ns.is_healthy,
            "response_time_ms": ns.response_time_ms,
            "last_check": ns.last_check.isoformat() if ns.last_check else None
        })
    
    return result


@app.post("/api/nameservers/health-check")
async def trigger_health_check(db: Session = Depends(get_db)):
    """手動觸發 DNS 伺服器健康檢查（並行執行）"""
    try:
        import asyncio
        from app.dns_checker import DNSChecker
        from datetime import datetime
        
        nameservers = db.query(Nameserver).all()
        checker = DNSChecker(timeout=3)  # 3 秒超時
        
        # 並行檢查所有 DNS 伺服器
        async def check_one(ns):
            try:
                result = await checker.resolve_a_record('google.com', str(ns.dns_server))
                return (ns, result, None)
            except Exception as e:
                return (ns, None, e)
        
        # 使用 asyncio.gather 並行執行所有檢查
        tasks = [check_one(ns) for ns in nameservers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        checked_count = 0
        healthy_count = 0
        
        # 處理結果
        for item in results:
            if isinstance(item, Exception):
                logger.error(f"Health check exception: {item}")
                continue
            
            ns, result, error = item
            
            if error:
                logger.error(f"Health check failed for {ns.dns_server}: {error}")
                ns.is_healthy = False
            elif result and result['status'] == 'success':
                ns.is_healthy = True
                ns.response_time_ms = result.get('response_time_ms')
                healthy_count += 1
            else:
                ns.is_healthy = False
            
            ns.last_check = local_now()
            checked_count += 1
        
        db.commit()
        
        return {
            "status": "success",
            "total": len(nameservers),
            "checked": checked_count,
            "healthy": healthy_count
        }
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/nameservers/stats")
async def nameservers_stats(db: Session = Depends(get_db)):
    """獲取 DNS 伺服器統計信息"""
    from sqlalchemy import func
    
    try:
        # 按國家統計
        by_country = db.query(
            Nameserver.country_code,
            func.count(Nameserver.id).label('count'),
            func.sum(func.cast(Nameserver.is_healthy, Integer)).label('healthy_count')
        ).filter(Nameserver.country_code.isnot(None)).group_by(Nameserver.country_code).all()
        
        # 按類型統計
        by_type = db.query(
            Nameserver.dns_type,
            func.count(Nameserver.id).label('count'),
            func.sum(func.cast(Nameserver.is_healthy, Integer)).label('healthy_count')
        ).filter(Nameserver.dns_type.isnot(None)).group_by(Nameserver.dns_type).all()
        
        # 按 ISP 統計
        by_isp = db.query(
            Nameserver.isp,
            Nameserver.country_code,
            func.count(Nameserver.id).label('count'),
            func.sum(func.cast(Nameserver.is_healthy, Integer)).label('healthy_count')
        ).filter(Nameserver.isp.isnot(None)).group_by(Nameserver.isp, Nameserver.country_code).all()
        
        return {
            "by_country": [
                {
                    "country_code": item.country_code or "Unknown",
                    "total": item.count,
                    "healthy": item.healthy_count or 0
                }
                for item in by_country
            ],
            "by_type": [
                {
                    "dns_type": item.dns_type or "Unknown",
                    "total": item.count,
                    "healthy": item.healthy_count or 0
                }
                for item in by_type
            ],
            "by_isp": [
                {
                    "isp": item.isp or "Unknown",
                    "country_code": item.country_code or "Unknown",
                    "total": item.count,
                    "healthy": item.healthy_count or 0
                }
                for item in by_isp
            ]
        }
    except Exception as e:
        logger.error(f"Error in nameservers_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    status_str = 'ok' if result['success_rate'] > 0.8 else 'warning'
    event = MonitoringEvent(
        domain_id=domain.id,
        event_type='dns_check',
        status=status_str,
        details=result
    )
    db.add(event)
    db.commit()
    
    # 如果有問題，創建或更新告警
    if status_str != 'ok':
        # Prepare checks data
        checks = {
            'global_dns': {
                'status': 'ok' if result.get('success_rate', 0) > 0.2 else 'fail',
                'resolved_ips': []
            },
            'isp_dns': {
                'failed_nameservers': result.get('failed_nameservers', []),
                'success_rate': result.get('success_rate', 0),
                'details': result
            },
            'securitytrails': {
                'ns_changed': False,
                'whois_changed': False
            },
            'uptime': {
                'keyword_match': True,
                'available': True
            }
        }
        
        # Run decision engine
        engine = AlertDecisionEngine()
        alert_data = engine.analyze(domain.domain, checks)
        
        if alert_data:
            # Check if similar alert exists
            existing_alert = db.query(Alert).filter(
                Alert.domain_id == domain.id,
                Alert.root_cause == alert_data['root_cause'],
                Alert.is_resolved == False
            ).first()
            
            if existing_alert:
                # Update existing alert
                existing_alert.last_seen = local_now()
                existing_alert.evidence = alert_data['evidence']  # 更新 evidence
                db.commit()
                logger.info(f"Updated existing alert for {domain.domain}")
            else:
                # Create new alert
                alert = Alert(
                    domain_id=domain.id,
                    alert_level=alert_data['alert_level'],
                    root_cause=alert_data['root_cause'],
                    evidence=alert_data['evidence']
                )
                db.add(alert)
                db.commit()
                logger.info(f"Created new alert for {domain.domain}")
    
    return DNSCheckResponse(
        domain=domain.domain,
        status='success',
        results=result,
        timestamp=local_now()
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
    
    # 將告警轉換為字典並加入域名資訊和摘要
    result = []
    for alert in alerts:
        # 生成證據摘要
        evidence_summary = generate_evidence_summary(alert)
        
        alert_dict = {
            "id": alert.id,
            "domain_id": alert.domain_id,
            "domain_name": alert.domain.domain if alert.domain else "Unknown",
            "alert_level": alert.alert_level,
            "root_cause": alert.root_cause,
            "evidence": alert.evidence,
            "evidence_summary": evidence_summary,  # 新增摘要字段
            "is_resolved": alert.is_resolved,
            "first_seen": alert.first_seen,
            "last_seen": alert.last_seen,
            "notified_at": alert.notified_at,
            "resolved_at": alert.resolved_at
        }
        result.append(alert_dict)
    
    return result


def generate_evidence_summary(alert):
    """生成告警證據摘要"""
    if not alert.evidence:
        return ""
    
    evidence = alert.evidence
    summary = []
    
    if alert.root_cause == 'country_blocked':
        # 特定國家被阻擋
        blocked_countries = evidence.get('blocked_countries', [])
        blocked_list = evidence.get('blocked_list', [])
        
        if blocked_list:
            summary.append(f"🚫 被阻擋國家: {', '.join(blocked_list)}")
        elif blocked_countries:
            country_names = {
                'VN': '越南',
                'ID': '印尼',
                'TW': '台灣',
                'HK': '香港',
                'JP': '日本',
                'KR': '韓國',
                'SG': '新加坡',
                'MY': '馬來西亞',
                'US': '美國',
                'CN': '中國'
            }
            countries = [country_names.get(c.get('country_code', ''), c.get('country_code', '')) for c in blocked_countries]
            summary.append(f"🚫 被阻擋國家: {', '.join(countries)}")
        
        overall_rate = evidence.get('overall_success_rate', 0)
        if overall_rate is not None:
            summary.append(f"整體成功率: {int(overall_rate * 100)}%")
    
    elif alert.root_cause == 'config_error':
        # DNS 配置錯誤
        failed_ns = evidence.get('failed_nameservers', [])
        success_rate = evidence.get('success_rate', 0)
        global_dns = evidence.get('global_dns', {})
        
        # 顯示失敗的 DNS 伺服器
        if failed_ns:
            failed_list = []
            for ns in failed_ns[:3]:
                server = ns.get('nameserver', 'Unknown')
                error = ns.get('error', '')
                if 'Could not contact DNS servers' in error or 'NXDOMAIN' in error:
                    failed_list.append(f"{server}")
                else:
                    failed_list.append(f"{server}")
            
            summary.append(f"❌ 失敗: {', '.join(failed_list)}")
            if len(failed_ns) > 3:
                summary.append(f"及其他 {len(failed_ns) - 3} 個")
        
        # 顯示成功率
        if success_rate is not None:
            summary.append(f"成功率: {int(success_rate * 100)}%")
        
        # 如果沒有詳細信息，顯示通用描述
        if not summary:
            summary.append("DNS 解析失敗，請檢查域名配置")
    
    elif alert.root_cause == 'domain_hijacked':
        old_ns = evidence.get('old_ns', [])
        new_ns = evidence.get('new_ns', [])
        if old_ns and new_ns:
            summary.append(f"🚨 NS 已變更")
            summary.append(f"舊: {', '.join(old_ns[:2])}")
            summary.append(f"新: {', '.join(new_ns[:2])}")
    
    elif alert.root_cause == 'isp_blocked':
        failed_isps = evidence.get('failed_isps', [])
        success_rate = evidence.get('success_rate', 0)
        if failed_isps:
            isp_names = ', '.join([isp.get('nameserver', '') for isp in failed_isps[:3]])
            summary.append(f"⚠️ 受影響 ISP: {isp_names}")
        summary.append(f"成功率: {int(success_rate * 100)}%")
    
    elif alert.root_cause == 'content_defacement':
        keyword = evidence.get('keyword_expected')
        http_status = evidence.get('http_status')
        if keyword:
            summary.append(f"⚠️ 關鍵字 \"{keyword}\" 未找到")
        if http_status:
            summary.append(f"HTTP 狀態: {http_status}")
    
    if not summary and alert.root_cause == 'config_error':
        summary.append('DNS 解析失敗，請檢查域名配置')
    
    return ' • '.join(summary)


@app.delete("/api/alerts/clear-all")
async def clear_all_alerts(db: Session = Depends(get_db)):
    """清除所有告警（用於重置系統）"""
    try:
        count = db.query(Alert).delete()
        db.commit()
        logger.info(f"Cleared {count} alerts")
        return {"status": "success", "cleared_count": count}
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events")
async def list_events(
    domain_id: int = None,
    event_type: str = None,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """列出監控事件 (包含域名資訊,預設最多 1000 筆)"""
    query = db.query(MonitoringEvent)
    
    if domain_id:
        query = query.filter(MonitoringEvent.domain_id == domain_id)
    if event_type:
        query = query.filter(MonitoringEvent.event_type == event_type)
    
    events = query.order_by(MonitoringEvent.timestamp.desc()).offset(skip).limit(limit).all()
    
    # 將事件轉換為字典並加入域名資訊
    result = []
    for event in events:
        event_dict = {
            "id": event.id,
            "domain_id": event.domain_id,
            "domain_name": event.domain.domain if event.domain else "Unknown",
            "event_type": event.event_type,
            "status": event.status,
            "details": event.details,
            "timestamp": event.timestamp
        }
        result.append(event_dict)
    
    return result


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

