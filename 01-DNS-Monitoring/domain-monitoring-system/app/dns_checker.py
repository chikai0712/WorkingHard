"""DNS checking module with async support"""
import asyncio
import aiodns
from typing import List, Dict, Optional
from datetime import datetime
import logging

from app.timezone_utils import local_now

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
            start_time = local_now()
            result = await resolver.query(domain, 'A')
            end_time = local_now()
            
            resolved_ips = [r.host for r in result]
            response_time = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                'status': 'success',
                'domain': domain,
                'nameserver': nameserver,
                'resolved_ips': resolved_ips,
                'response_time_ms': response_time,
                'timestamp': local_now().isoformat()
            }
            
        except aiodns.error.DNSError as e:
            logger.warning(f"DNS query failed for {domain} via {nameserver}: {e}")
            return {
                'status': 'error',
                'domain': domain,
                'nameserver': nameserver,
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': local_now().isoformat()
            }
        except Exception as e:
            logger.error(f"Unexpected error querying {domain} via {nameserver}: {e}")
            return {
                'status': 'error',
                'domain': domain,
                'nameserver': nameserver,
                'error': str(e),
                'error_type': 'UnexpectedError',
                'timestamp': local_now().isoformat()
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
                'timestamp': local_now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"NS query failed for {domain}: {e}")
            return {
                'status': 'error',
                'domain': domain,
                'error': str(e),
                'timestamp': local_now().isoformat()
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
                    'timestamp': local_now().isoformat()
                }
        
        return {
            'status': 'error',
            'original_domain': domain,
            'error': 'CNAME chain too deep (max 10 levels)',
            'cname_chain': cname_chain,
            'timestamp': local_now().isoformat()
        }
    
    async def check_domain_multi_ns(self, domain: str, nameservers: List[str], expected_ips: Optional[List[str]] = None) -> Dict:
        """
        使用多個 DNS 伺服器檢查網域
        
        Args:
            domain: 網域名稱
            nameservers: DNS 伺服器列表
            expected_ips: 預期的 IP 白名單（可選，None 表示不檢查白名單）
            
        Returns:
            Dict with aggregated results
        """
        tasks = [self.resolve_a_record(domain, ns) for ns in nameservers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = 0
        warning_count = 0  # 解析成功但不在白名單
        failed_nameservers = []
        valid_resolutions = []
        warning_resolutions = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_nameservers.append({
                    'nameserver': nameservers[i],
                    'error': str(result),
                    'severity': 'error'
                })
                continue
            
            if result['status'] == 'success':
                resolved_ips = result['resolved_ips']
                
                # 如果沒有設定白名單，所有成功解析都算有效
                if not expected_ips:
                    success_count += 1
                    valid_resolutions.append(result)
                else:
                    # 有白名單時才檢查
                    is_valid = any(ip in expected_ips for ip in resolved_ips)
                    
                    if is_valid:
                        success_count += 1
                        valid_resolutions.append(result)
                    else:
                        # 解析成功但不在白名單 = warning（不算完全失敗）
                        warning_count += 1
                        warning_resolutions.append(result)
                        failed_nameservers.append({
                            'nameserver': nameservers[i],
                            'resolved_ips': resolved_ips,
                            'reason': 'IP not in whitelist',
                            'severity': 'warning'
                        })
            else:
                failed_nameservers.append({
                    'nameserver': nameservers[i],
                    'error': result.get('error', 'Unknown error'),
                    'severity': 'error'
                })
        
        # 成功率計算：成功解析的比例
        total_resolved = success_count + warning_count
        resolution_rate = total_resolved / len(nameservers) if nameservers else 0
        
        # 白名單匹配率：在白名單內的比例
        whitelist_match_rate = success_count / len(nameservers) if nameservers else 0
        
        return {
            'domain': domain,
            'total_checks': len(nameservers),
            'success_count': success_count,
            'warning_count': warning_count,
            'resolution_rate': resolution_rate,  # DNS 解析成功率
            'whitelist_match_rate': whitelist_match_rate,  # 白名單匹配率
            'success_rate': whitelist_match_rate,  # 向後兼容
            'failed_nameservers': failed_nameservers,
            'valid_resolutions': valid_resolutions,
            'warning_resolutions': warning_resolutions,
            'has_whitelist': expected_ips is not None and len(expected_ips) > 0,
            'timestamp': local_now().isoformat()
        }
    
    async def check_domain_by_country(self, domain: str, nameservers_by_country: Dict[str, List[str]], expected_ips: Optional[List[str]] = None) -> Dict:
        """
        按國家分組檢查網域（用於識別地區性阻擋）
        
        Args:
            domain: 網域名稱
            nameservers_by_country: 按國家分組的 DNS 伺服器 {'VN': ['ip1', 'ip2'], 'ID': ['ip3'], ...}
            expected_ips: 預期的 IP 白名單（可選）
            
        Returns:
            Dict with results grouped by country
        """
        country_results = {}
        blocked_countries = []
        
        for country_code, ns_list in nameservers_by_country.items():
            if not ns_list:
                continue
            
            # 檢查該國家的所有 DNS
            result = await self.check_domain_multi_ns(domain, ns_list, expected_ips)
            
            # 判斷該國家是否被阻擋
            # 標準：白名單匹配率 < 50% 視為該國家被阻擋
            is_blocked = result['whitelist_match_rate'] < 0.5 if expected_ips else result['resolution_rate'] < 0.5
            
            country_results[country_code] = {
                'total_checks': result['total_checks'],
                'success_count': result['success_count'],
                'resolution_rate': result['resolution_rate'],
                'whitelist_match_rate': result['whitelist_match_rate'],
                'is_blocked': is_blocked,
                'failed_nameservers': result['failed_nameservers']
            }
            
            if is_blocked:
                blocked_countries.append({
                    'country_code': country_code,
                    'success_rate': result['whitelist_match_rate'] if expected_ips else result['resolution_rate'],
                    'failed_count': len(result['failed_nameservers'])
                })
        
        # 計算整體統計
        total_checks = sum(r['total_checks'] for r in country_results.values())
        total_success = sum(r['success_count'] for r in country_results.values())
        overall_rate = total_success / total_checks if total_checks > 0 else 0
        
        return {
            'domain': domain,
            'country_results': country_results,
            'blocked_countries': blocked_countries,
            'overall_success_rate': overall_rate,
            'total_countries_checked': len(country_results),
            'blocked_countries_count': len(blocked_countries),
            'has_whitelist': expected_ips is not None and len(expected_ips) > 0,
            'timestamp': local_now().isoformat()
        }

