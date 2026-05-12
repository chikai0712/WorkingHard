"""Test decision engine logic"""
import pytest
from app.decision_engine import AlertDecisionEngine


def test_domain_hijacked_detection():
    """測試域名劫持偵測"""
    engine = AlertDecisionEngine()
    
    checks = {
        'securitytrails': {
            'ns_changed': True,
            'old_ns': ['ns1.example.com'],
            'new_ns': ['malicious.ns.com']
        },
        'global_dns': {'status': 'ok'},
        'isp_dns': {'success_rate': 1.0, 'failed_isps': []},
        'uptime': {'keyword_match': True, 'available': True}
    }
    
    alert = engine.analyze('example.com', checks)
    
    assert alert is not None
    assert alert['alert_level'] == 'P0'
    assert alert['root_cause'] == 'domain_hijacked'


def test_isp_blocked_detection():
    """測試 ISP 封鎖偵測"""
    engine = AlertDecisionEngine()
    
    checks = {
        'securitytrails': {'ns_changed': False},
        'global_dns': {'status': 'ok', 'resolved_ips': ['1.2.3.4']},
        'isp_dns': {
            'success_rate': 0.3,
            'failed_isps': [
                {'nameserver': '202.96.128.86', 'reason': 'IP not in whitelist'}
            ]
        },
        'uptime': {'keyword_match': True, 'available': True}
    }
    
    alert = engine.analyze('example.com', checks)
    
    assert alert is not None
    assert alert['alert_level'] == 'P1'
    assert alert['root_cause'] == 'isp_blocked'


def test_content_defacement_detection():
    """測試內容竄改偵測"""
    engine = AlertDecisionEngine()
    
    checks = {
        'securitytrails': {'ns_changed': False},
        'global_dns': {'status': 'ok'},
        'isp_dns': {'success_rate': 1.0, 'failed_isps': []},
        'uptime': {
            'keyword_match': False,
            'available': True,
            'http_status': 200
        }
    }
    
    alert = engine.analyze('example.com', checks)
    
    assert alert is not None
    assert alert['alert_level'] == 'P1'
    assert alert['root_cause'] == 'content_defacement'


def test_config_error_detection():
    """測試配置錯誤偵測"""
    engine = AlertDecisionEngine()
    
    checks = {
        'securitytrails': {'ns_changed': False},
        'global_dns': {'status': 'fail'},
        'isp_dns': {'success_rate': 0.0, 'failed_isps': []},
        'uptime': {'keyword_match': False, 'available': False}
    }
    
    alert = engine.analyze('example.com', checks)
    
    assert alert is not None
    assert alert['alert_level'] == 'P2'
    assert alert['root_cause'] == 'config_error'


def test_no_alert_when_all_ok():
    """測試正常情況不產生告警"""
    engine = AlertDecisionEngine()
    
    checks = {
        'securitytrails': {'ns_changed': False, 'whois_changed': False},
        'global_dns': {'status': 'ok'},
        'isp_dns': {'success_rate': 1.0, 'failed_isps': []},
        'uptime': {'keyword_match': True, 'available': True}
    }
    
    alert = engine.analyze('example.com', checks)
    
    assert alert is None


def test_format_alert_message():
    """測試告警訊息格式化"""
    engine = AlertDecisionEngine()
    
    alert = {
        'alert_level': 'P1',
        'root_cause': 'isp_blocked',
        'title': '區域性 ISP 封鎖',
        'description': '測試描述',
        'evidence': {'test': 'data'},
        'recommendation': '測試建議',
        'timestamp': '2026-02-12T00:00:00'
    }
    
    message = engine.format_alert_message('example.com', alert)
    
    assert 'example.com' in message
    assert 'P1' in message
    assert '區域性 ISP 封鎖' in message
    assert 'isp_blocked' in message

