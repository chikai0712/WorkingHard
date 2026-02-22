"""DNS checking module with async support"""
import asyncio
import aiodns
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DNSChecker:
    """DNS 查詢核心模組"""
    
    def __init__(self, timeout: int = 3, max_retries: int = 2):
        self.timeout = timeout
        self.max_retries = max_retries
    
    async def resolve_a_record(self, domain: str, nameserver: str = "8.8.8.8") -> Dict:
        """
        解析 A 記錄
        
        Args:
            domain: 網域名稱
            nameserver: DNS 伺服器
            
        Returns:
            Dict with resolved IPs and metadata
        """
        resolver = aiodns.DNSResolver(nameservers=[nameserver], timeout=self.timeout)
        
        try:
            start_time = datetime.utcnow()
            result = await resolver.query(domain, 'A')
            end_time = datetime.utcnow()
            
            resolved_ips = [r.host for r in result]
            response_time = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                'status': 'success',
                'domain': domain,
                'nameserver': nameserver,
                'resolved_ips': resolved_ips,
                'response_time_ms': response_time,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except aiodns.error.DNSError as e:
            logger.warning(f"DNS query failed for {domain} via {nameserver}: {e}")
            return {
                'status': 'error',
                'domain': domain,
                'nameserver': nameserver,
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Unexpected error querying {domain} via {nameserver}: {e}")
            return {
                'status': 'error',
                'domain': domain,
                'nameserver': nameserver,
                'error': str(e),
                'error_type': 'UnexpectedError',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def resolve_ns_record(self, domain: str, nameserver: str = "8.8.8.8") -> Dict:
        """
        解析 NS 記錄
        
        Args:
            domain: 網域名稱
            nameserver: DNS 伺服器
            
        Returns:
            Dict with NS records
        """
        resolver = aiodns.DNSResolver(nameservers=[nameserver], timeout=self.timeout)
        
        try:
            result = await resolver.query(domain, 'NS')
            ns_records = [r.host for r in result]
            
            return {
                'status': 'success',
                'domain': domain,
                'ns_records': ns_records,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"NS query failed for {domain}: {e}")
            return {
                'status': 'error',
                'domain': domain,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def resolve_cname_chain(self, domain: str, nameserver: str = "8.8.8.8", max_depth: int = 10) -> Dict:
        """
        解析 CNAME 鏈 (遞迴追蹤)
        
        Args:
            domain: 網域名稱
            nameserver: DNS 伺服器
            max_depth: 最大遞迴深度
            
        Returns:
            Dict with CNAME chain and final IPs
        """
        resolver = aiodns.DNSResolver(nameservers=[nameserver], timeout=self.timeout)
        cname_chain = []
        current_domain = domain
        
        for depth in range(max_depth):
            try:
                # Try CNAME first
                result = await resolver.query(current_domain, 'CNAME')
                cname_target = result.cname
                cname_chain.append({
                    'domain': current_domain,
                    'cname': cname_target,
                    'depth': depth
                })
                current_domain = cname_target
                
            except aiodns.error.DNSError:
                # No CNAME, try A record
                a_result = await self.resolve_a_record(current_domain, nameserver)
                
                return {
                    'status': 'success',
                    'original_domain': domain,
                    'cname_chain': cname_chain,
                    'final_domain': current_domain,
                    'final_ips': a_result.get('resolved_ips', []),
                    'chain_length': len(cname_chain),
                    'timestamp': datetime.utcnow().isoformat()
                }
        
        return {
            'status': 'error',
            'original_domain': domain,
            'error': 'CNAME chain too deep (max 10 levels)',
            'cname_chain': cname_chain,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def check_domain_multi_ns(self, domain: str, nameservers: List[str], expected_ips: List[str]) -> Dict:
        """
        使用多個 DNS 伺服器檢查網域
        
        Args:
            domain: 網域名稱
            nameservers: DNS 伺服器列表
            expected_ips: 預期的 IP 白名單
            
        Returns:
            Dict with aggregated results
        """
        tasks = [self.resolve_a_record(domain, ns) for ns in nameservers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = 0
        failed_nameservers = []
        valid_resolutions = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_nameservers.append({
                    'nameserver': nameservers[i],
                    'error': str(result)
                })
                continue
            
            if result['status'] == 'success':
                resolved_ips = result['resolved_ips']
                is_valid = any(ip in expected_ips for ip in resolved_ips)
                
                if is_valid:
                    success_count += 1
                    valid_resolutions.append(result)
                else:
                    failed_nameservers.append({
                        'nameserver': nameservers[i],
                        'resolved_ips': resolved_ips,
                        'reason': 'IP not in whitelist'
                    })
            else:
                failed_nameservers.append({
                    'nameserver': nameservers[i],
                    'error': result.get('error', 'Unknown error')
                })
        
        success_rate = success_count / len(nameservers) if nameservers else 0
        
        return {
            'domain': domain,
            'total_checks': len(nameservers),
            'success_count': success_count,
            'success_rate': success_rate,
            'failed_nameservers': failed_nameservers,
            'valid_resolutions': valid_resolutions,
            'timestamp': datetime.utcnow().isoformat()
        }

