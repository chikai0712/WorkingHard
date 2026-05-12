"""Test DNS checker functionality"""
import pytest
import asyncio
from app.dns_checker import DNSChecker


@pytest.mark.asyncio
async def test_resolve_a_record():
    """測試 A 記錄解析"""
    checker = DNSChecker()
    result = await checker.resolve_a_record("google.com", "8.8.8.8")
    
    assert result['status'] == 'success'
    assert 'resolved_ips' in result
    assert len(result['resolved_ips']) > 0
    assert 'response_time_ms' in result


@pytest.mark.asyncio
async def test_resolve_ns_record():
    """測試 NS 記錄解析"""
    checker = DNSChecker()
    result = await checker.resolve_ns_record("google.com", "8.8.8.8")
    
    assert result['status'] == 'success'
    assert 'ns_records' in result
    assert len(result['ns_records']) > 0


@pytest.mark.asyncio
async def test_check_domain_multi_ns():
    """測試多 DNS 伺服器檢查"""
    checker = DNSChecker()
    nameservers = ["8.8.8.8", "1.1.1.1"]
    expected_ips = ["142.250.185.46"]  # Google IP (可能變動)
    
    result = await checker.check_domain_multi_ns(
        domain="google.com",
        nameservers=nameservers,
        expected_ips=expected_ips
    )
    
    assert 'domain' in result
    assert result['domain'] == 'google.com'
    assert 'success_rate' in result
    assert result['total_checks'] == len(nameservers)


@pytest.mark.asyncio
async def test_resolve_nonexistent_domain():
    """測試不存在的網域"""
    checker = DNSChecker()
    result = await checker.resolve_a_record("this-domain-does-not-exist-12345.com", "8.8.8.8")
    
    assert result['status'] == 'error'
    assert 'error' in result

