"""Celery tasks for scheduled monitoring"""
from celery import Celery
from celery.schedules import crontab
from sqlalchemy.orm import Session
import asyncio
import logging

from app.config import settings
from app.database import SessionLocal
from app.models import Domain, Nameserver, MonitoringEvent, Alert
from app.dns_checker import DNSChecker
from app.decision_engine import AlertDecisionEngine
from app.notifier import SlackNotifier
from app.timezone_utils import local_now

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'domain_monitoring',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Taipei',  # 使用台北時區
    enable_utc=False,  # 不使用 UTC，使用本地時區
)


@celery_app.task(name='check_all_domains')
def check_all_domains():
    """定期檢查所有網域（每 5 分鐘）"""
    db = SessionLocal()
    try:
        # 只檢查啟用且未暫停的域名
        now = local_now()
        domains = db.query(Domain).filter(
            Domain.is_active == True,
            (Domain.paused_until == None) | (Domain.paused_until <= now)
        ).all()
        
        logger.info(f"Starting DNS check for {len(domains)} domains")
        
        # 不在這裡清除暫停狀態，統一由每天 0:00 的任務處理
        for domain in domains:
            check_single_domain.delay(domain.id)
        
        return {"status": "scheduled", "domains_count": len(domains)}
    finally:
        db.close()


@celery_app.task(name='check_single_domain')
def check_single_domain(domain_id: int):
    """檢查單一網域"""
    db = SessionLocal()
    try:
        domain = db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            logger.error(f"Domain {domain_id} not found")
            return
        
        # Get healthy nameservers grouped by country
        nameservers = db.query(Nameserver).filter(Nameserver.is_healthy == True).all()
        
        # 按國家分組 DNS 伺服器
        nameservers_by_country = {}
        for ns in nameservers:
            country = ns.country_code or 'GLOBAL'
            if country not in nameservers_by_country:
                nameservers_by_country[country] = []
            nameservers_by_country[country].append(str(ns.dns_server))
        
        # Run DNS check with country grouping
        checker = DNSChecker()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            checker.check_domain_by_country(
                domain=domain.domain,
                nameservers_by_country=nameservers_by_country,
                expected_ips=domain.expected_ips if domain.expected_ips else None
            )
        )
        loop.close()
        
        # 判斷狀態
        overall_rate = result.get('overall_success_rate', 0)
        blocked_countries = result.get('blocked_countries', [])
        has_whitelist = result.get('has_whitelist', False)
        
        # 狀態判斷：整體成功率 >= 50% = OK
        status = 'ok' if overall_rate >= 0.5 else 'warning'
        
        # 如果有國家被阻擋，即使整體成功率高也要標記為 warning
        if blocked_countries:
            status = 'warning'
        
        event = MonitoringEvent(
            domain_id=domain.id,
            event_type='dns_check',
            status=status,
            details=result
        )
        db.add(event)
        db.commit()
        
        # Run decision engine if there's an issue
        if status != 'ok':
            analyze_and_alert.delay(domain.id, result)
        else:
            # 如果狀態正常,解決該域名的所有未解決告警
            resolve_domain_alerts.delay(domain.id)
        
        logger.info(f"Checked domain {domain.domain}: {status} (overall: {overall_rate:.1%}, blocked countries: {len(blocked_countries)})")
        return {
            "domain": domain.domain, 
            "status": status, 
            "overall_rate": overall_rate,
            "blocked_countries": [c['country_code'] for c in blocked_countries]
        }
        
    except Exception as e:
        logger.error(f"Error checking domain {domain_id}: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(name='resolve_domain_alerts')
def resolve_domain_alerts(domain_id: int):
    """解決域名的所有未解決告警(當狀態恢復正常時)"""
    db = SessionLocal()
    try:
        from datetime import datetime
        
        # 找出該域名所有未解決的告警
        unresolved_alerts = db.query(Alert).filter(
            Alert.domain_id == domain_id,
            Alert.is_resolved == False
        ).all()
        
        if unresolved_alerts:
            for alert in unresolved_alerts:
                alert.is_resolved = True
                alert.resolved_at = local_now()
            
            db.commit()
            logger.info(f"Resolved {len(unresolved_alerts)} alerts for domain {domain_id}")
        
    except Exception as e:
        logger.error(f"Error resolving alerts for domain {domain_id}: {e}")
    finally:
        db.close()


@celery_app.task(name='analyze_and_alert')
def analyze_and_alert(domain_id: int, dns_result: dict):
    """分析結果並發送告警"""
    db = SessionLocal()
    try:
        domain = db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            return
        
        # 提取按國家分組的結果
        country_results = dns_result.get('country_results', {})
        blocked_countries = dns_result.get('blocked_countries', [])
        overall_rate = dns_result.get('overall_success_rate', 0)
        has_whitelist = dns_result.get('has_whitelist', False)
        
        # 全球 DNS 狀態：整體成功率 >= 50% 就算正常
        global_dns_ok = overall_rate >= 0.5
        
        # 準備失敗的 ISP 列表（用於告警詳情）
        failed_isps = []
        for country_code, country_data in country_results.items():
            if country_data.get('is_blocked'):
                for failed_ns in country_data.get('failed_nameservers', []):
                    failed_isps.append({
                        'nameserver': failed_ns.get('nameserver'),
                        'country': country_code,
                        'error': failed_ns.get('error', failed_ns.get('reason', 'Unknown')),
                        'severity': failed_ns.get('severity', 'error')
                    })
        
        # Prepare checks data
        checks = {
            'global_dns': {
                'status': 'ok' if global_dns_ok else 'fail',
                'resolved_ips': [],
                'overall_success_rate': overall_rate
            },
            'isp_dns': {
                'failed_isps': failed_isps,
                'success_rate': overall_rate,
                'blocked_countries': blocked_countries,
                'country_results': country_results,
                'has_whitelist': has_whitelist,
                'details': dns_result
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
            # Check if similar alert exists (不限時間,只要未解決就更新)
            from datetime import datetime
            
            existing_alert = db.query(Alert).filter(
                Alert.domain_id == domain.id,
                Alert.root_cause == alert_data['root_cause'],
                Alert.is_resolved == False
            ).first()
            
            if existing_alert:
                # Update existing alert
                existing_alert.last_seen = local_now()
                existing_alert.evidence = alert_data['evidence']  # 更新證據
                db.commit()
                logger.info(f"Updated existing alert for {domain.domain}: {alert_data['root_cause']}")
            else:
                # Create new alert
                alert = Alert(
                    domain_id=domain.id,
                    alert_level=alert_data['alert_level'],
                    root_cause=alert_data['root_cause'],
                    evidence=alert_data['evidence']  # 只存儲 evidence 部分
                )
                db.add(alert)
                db.commit()
                
                # Send notification
                notifier = SlackNotifier()
                message = engine.format_alert_message(domain.domain, alert_data)
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    notifier.send_alert(message, domain.domain, alert_data['alert_level'])
                )
                loop.close()
                
                alert.notified_at = local_now()
                db.commit()
                
                logger.info(f"Created and sent alert for {domain.domain}: {alert_data['root_cause']}")
        
    except Exception as e:
        logger.error(f"Error in analyze_and_alert: {e}")
    finally:
        db.close()


@celery_app.task(name='health_check_nameservers')
def health_check_nameservers():
    """檢查所有 DNS 伺服器的健康狀態"""
    db = SessionLocal()
    try:
        nameservers = db.query(Nameserver).all()
        checker = DNSChecker()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        for ns in nameservers:
            try:
                result = loop.run_until_complete(
                    checker.resolve_a_record('google.com', str(ns.dns_server))
                )
                
                if result['status'] == 'success':
                    ns.is_healthy = True
                    ns.response_time_ms = result.get('response_time_ms')
                else:
                    ns.is_healthy = False
                
                from datetime import datetime
                ns.last_check = local_now()
                
            except Exception as e:
                logger.error(f"Health check failed for {ns.dns_server}: {e}")
                ns.is_healthy = False
        
        loop.close()
        db.commit()
        
        healthy_count = sum(1 for ns in nameservers if ns.is_healthy)
        logger.info(f"Nameserver health check: {healthy_count}/{len(nameservers)} healthy")
        
        return {"total": len(nameservers), "healthy": healthy_count}
        
    finally:
        db.close()


@celery_app.task(name='check_568win_uptime')
def check_568win_uptime():
    """每 10 分鐘檢查 568win 域名的網站可用性"""
    db = SessionLocal()
    try:
        from app.uptime_checker import UptimeChecker
        
        # 查詢所有 568win 相關且啟用的域名
        domains = db.query(Domain).filter(
            Domain.is_active == True,
            Domain.domain.like('%568win%')
        ).all()
        
        if not domains:
            logger.info("No 568win domains found for uptime check")
            return {"status": "no_domains"}
        
        logger.info(f"Checking uptime for {len(domains)} 568win domains")
        
        checker = UptimeChecker()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        checked_count = 0
        down_count = 0
        content_issues = 0
        
        for domain in domains:
            try:
                # 檢查網站可用性和關鍵字
                result = loop.run_until_complete(
                    checker.check_multiple_protocols(
                        domain.domain,
                        keyword=domain.keyword  # 使用資料庫中設定的關鍵字
                    )
                )
                
                best = result['best_result']
                checked_count += 1
                
                # 判斷狀態
                is_down = not best.get('available', False)
                keyword_mismatch = (
                    domain.keyword and 
                    best.get('available') and 
                    not best.get('keyword_match', True)
                )
                
                if is_down:
                    down_count += 1
                if keyword_mismatch:
                    content_issues += 1
                
                # 記錄監控事件
                status = 'ok'
                if is_down:
                    status = 'critical'
                elif keyword_mismatch:
                    status = 'warning'
                
                event = MonitoringEvent(
                    domain_id=domain.id,
                    event_type='uptime_check',
                    status=status,
                    details=result
                )
                db.add(event)
                
                # 如果有問題,觸發告警分析
                if is_down or keyword_mismatch:
                    # 準備檢查數據
                    checks = {
                        'global_dns': {'status': 'ok', 'resolved_ips': []},
                        'isp_dns': {'failed_isps': [], 'success_rate': 1.0, 'details': {}},
                        'securitytrails': {'ns_changed': False, 'whois_changed': False},
                        'uptime': {
                            'available': best.get('available', False),
                            'keyword_match': best.get('keyword_match', True),
                            'keyword_expected': domain.keyword,
                            'keyword_found': best.get('keyword_found', False),
                            'http_status': best.get('http_status'),
                            'error': best.get('error')
                        }
                    }
                    
                    # 使用決策引擎分析
                    engine = AlertDecisionEngine()
                    alert_data = engine.analyze(domain.domain, checks)
                    
                    if alert_data:
                        from datetime import datetime
                        
                        # 檢查是否已有相同告警
                        existing_alert = db.query(Alert).filter(
                            Alert.domain_id == domain.id,
                            Alert.root_cause == alert_data['root_cause'],
                            Alert.is_resolved == False
                        ).first()
                        
                        if existing_alert:
                            # 更新現有告警
                            existing_alert.last_seen = local_now()
                        else:
                            # 創建新告警
                            alert = Alert(
                                domain_id=domain.id,
                                alert_level=alert_data['alert_level'],
                                root_cause=alert_data['root_cause'],
                                evidence=alert_data['evidence']  # 只存儲 evidence 部分
                            )
                            db.add(alert)
                            db.commit()
                            
                            # 發送通知
                            notifier = SlackNotifier()
                            message = engine.format_alert_message(domain.domain, alert_data)
                            loop.run_until_complete(
                                notifier.send_alert(message, domain.domain, alert_data['alert_level'])
                            )
                            
                            alert.notified_at = local_now()
                            
                            logger.warning(f"Uptime issue detected for {domain.domain}: {alert_data['root_cause']}")
                
            except Exception as e:
                logger.error(f"Uptime check failed for {domain.domain}: {e}")
        
        loop.close()
        db.commit()
        
        logger.info(f"Uptime check completed: {checked_count} domains, {down_count} down, {content_issues} content issues")
        
        return {
            "status": "completed",
            "domains_checked": checked_count,
            "down_count": down_count,
            "content_issues": content_issues
        }
        
    except Exception as e:
        logger.error(f"Error in check_568win_uptime: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task(name='check_568win_domains_securitytrails')
def check_568win_domains_securitytrails():
    """每天檢查 568win 相關域名的 NS 記錄 (使用 SecurityTrails API)"""
    db = SessionLocal()
    try:
        from app.securitytrails import SecurityTrailsChecker
        
        # 查詢所有 568win 相關的域名
        domains = db.query(Domain).filter(
            Domain.is_active == True,
            Domain.domain.like('%568win%')
        ).all()
        
        if not domains:
            logger.info("No 568win domains found")
            return {"status": "no_domains"}
        
        logger.info(f"Checking {len(domains)} 568win domains with SecurityTrails")
        
        checker = SecurityTrailsChecker()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        checked_count = 0
        alerts_created = 0
        
        for domain in domains:
            try:
                # 檢查 NS 記錄
                ns_result = loop.run_until_complete(
                    checker.check_ns_records(domain.domain)
                )
                
                # 檢查 WHOIS
                whois_result = loop.run_until_complete(
                    checker.check_whois(domain.domain)
                )
                
                checked_count += 1
                
                # 如果發現 NS 變動,立即產生告警
                if ns_result.get('ns_changed'):
                    checks = {
                        'global_dns': {'status': 'ok', 'resolved_ips': []},
                        'isp_dns': {'failed_isps': [], 'success_rate': 1.0, 'details': {}},
                        'securitytrails': {
                            'ns_changed': True,
                            'old_ns': ns_result.get('history', [{}])[1].get('values', []) if len(ns_result.get('history', [])) > 1 else [],
                            'new_ns': ns_result.get('current_ns', []),
                            'changed_at': ns_result.get('last_change'),
                            'whois_changed': whois_result.get('whois_changed', False)
                        },
                        'uptime': {'keyword_match': True, 'available': True}
                    }
                    
                    # 使用決策引擎產生告警
                    engine = AlertDecisionEngine()
                    alert_data = engine.analyze(domain.domain, checks)
                    
                    if alert_data:
                        from datetime import datetime
                        
                        # 檢查是否已有相同告警
                        existing_alert = db.query(Alert).filter(
                            Alert.domain_id == domain.id,
                            Alert.root_cause == alert_data['root_cause'],
                            Alert.is_resolved == False
                        ).first()
                        
                        if not existing_alert:
                            alert = Alert(
                                domain_id=domain.id,
                                alert_level=alert_data['alert_level'],
                                root_cause=alert_data['root_cause'],
                                evidence=alert_data['evidence']  # 只存儲 evidence 部分
                            )
                            db.add(alert)
                            db.commit()
                            
                            # 發送通知
                            notifier = SlackNotifier()
                            message = engine.format_alert_message(domain.domain, alert_data)
                            loop.run_until_complete(
                                notifier.send_alert(message, domain.domain, alert_data['alert_level'])
                            )
                            
                            alert.notified_at = local_now()
                            db.commit()
                            
                            alerts_created += 1
                            logger.warning(f"NS changed detected for {domain.domain}!")
                
                # 記錄檢查事件
                event = MonitoringEvent(
                    domain_id=domain.id,
                    event_type='securitytrails_check',
                    status='ok' if not ns_result.get('ns_changed') else 'critical',
                    details={
                        'ns_check': ns_result,
                        'whois_check': whois_result
                    }
                )
                db.add(event)
                
            except Exception as e:
                logger.error(f"SecurityTrails check failed for {domain.domain}: {e}")
        
        loop.close()
        db.commit()
        
        logger.info(f"SecurityTrails check completed: {checked_count} domains checked, {alerts_created} alerts created")
        
        return {
            "status": "completed",
            "domains_checked": checked_count,
            "alerts_created": alerts_created
        }
        
    except Exception as e:
        logger.error(f"Error in check_568win_domains_securitytrails: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task(name='check_and_pause_no_record_domains')
def check_and_pause_no_record_domains():
    """每天 0:00 檢測無 DNS 記錄的域名並暫停到明天 0:00"""
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        
        # 先清除所有暫停狀態（每天 0:00 重置）
        logger.info("Clearing all paused domains for daily check")
        paused_domains = db.query(Domain).filter(Domain.paused_until != None).all()
        cleared_count = len(paused_domains)
        for domain in paused_domains:
            domain.paused_until = None
            domain.pause_reason = None
            logger.info(f"Cleared pause status for {domain.domain}")
        
        db.commit()
        
        # 查詢所有啟用的域名
        domains = db.query(Domain).filter(Domain.is_active == True).all()
        
        if not domains:
            logger.info("No active domains to check")
            return {"status": "no_domains"}
        
        logger.info(f"Checking {len(domains)} domains for DNS records")
        
        # 獲取健康的 DNS 伺服器
        nameservers = db.query(Nameserver).filter(Nameserver.is_healthy == True).all()
        ns_list = [ns.dns_server for ns in nameservers]
        
        if not ns_list:
            logger.error("No healthy nameservers available")
            return {"status": "error", "error": "No healthy nameservers"}
        
        checker = DNSChecker()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        checked_count = 0
        paused_count = 0
        now = local_now()
        
        # 計算明天 0:00 的時間
        tomorrow = now + timedelta(days=1)
        next_midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for domain in domains:
            try:
                # 執行 DNS 檢查（不檢查白名單，只看能否解析）
                result = loop.run_until_complete(
                    checker.check_domain_multi_ns(
                        domain=domain.domain,
                        nameservers=ns_list,
                        expected_ips=None  # 不檢查白名單
                    )
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
        
        loop.close()
        db.commit()
        
        logger.info(f"Daily check completed: {cleared_count} domains unpaused, {checked_count} domains checked, {paused_count} domains paused until next midnight")
        
        return {
            "status": "completed",
            "domains_cleared": cleared_count,
            "domains_checked": checked_count,
            "domains_paused": paused_count
        }
        
    except Exception as e:
        logger.error(f"Error in check_and_pause_no_record_domains: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'check-all-domains-every-5-minutes': {
        'task': 'check_all_domains',
        'schedule': 300.0,  # 5 minutes
    },
    'health-check-nameservers-every-hour': {
        'task': 'health_check_nameservers',
        'schedule': 3600.0,  # 1 hour
    },
    'check-568win-securitytrails-daily': {
        'task': 'check_568win_domains_securitytrails',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨 2:00 執行
    },
    'check-568win-uptime-every-10-minutes': {
        'task': 'check_568win_uptime',
        'schedule': 600.0,  # 每 10 分鐘執行
    },
    'check-and-pause-no-record-domains-daily': {
        'task': 'check_and_pause_no_record_domains',
        'schedule': crontab(hour=0, minute=0),  # 每天凌晨 0:00 執行
    },
}

