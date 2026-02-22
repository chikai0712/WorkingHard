"""Uptime and content monitoring module"""
import aiohttp
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class UptimeChecker:
    """網站可用性和內容監控"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        
    async def check_uptime(
        self, 
        domain: str, 
        keyword: Optional[str] = None,
        protocol: str = 'https'
    ) -> Dict:
        """
        檢查網站可用性和關鍵字
        
        Args:
            domain: 網域名稱
            keyword: 預期的關鍵字 (用於檢測內容竄改)
            protocol: http 或 https
            
        Returns:
            {
                'status': 'success/error',
                'available': bool,
                'http_status': int,
                'response_time_ms': int,
                'keyword_match': bool,
                'keyword_found': bool,
                'content_length': int,
                'error': str (if error)
            }
        """
        url = f"{protocol}://{domain}"
        start_time = datetime.utcnow()
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    url, 
                    allow_redirects=True,
                    ssl=False  # 忽略 SSL 證書錯誤
                ) as response:
                    end_time = datetime.utcnow()
                    response_time = int((end_time - start_time).total_seconds() * 1000)
                    
                    # 讀取內容
                    content = await response.text()
                    content_length = len(content)
                    
                    # 檢查關鍵字
                    keyword_found = False
                    keyword_match = True
                    
                    if keyword:
                        keyword_found = keyword.lower() in content.lower()
                        keyword_match = keyword_found
                    
                    # 判斷是否可用
                    available = 200 <= response.status < 400
                    
                    return {
                        'status': 'success',
                        'available': available,
                        'http_status': response.status,
                        'response_time_ms': response_time,
                        'keyword_match': keyword_match,
                        'keyword_found': keyword_found,
                        'keyword_expected': keyword,
                        'content_length': content_length,
                        'final_url': str(response.url),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
        except asyncio.TimeoutError:
            return {
                'status': 'error',
                'available': False,
                'error': 'Timeout',
                'error_type': 'timeout',
                'timestamp': datetime.utcnow().isoformat()
            }
        except aiohttp.ClientConnectorError as e:
            return {
                'status': 'error',
                'available': False,
                'error': f'Connection failed: {str(e)}',
                'error_type': 'connection_error',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Uptime check failed for {domain}: {e}")
            return {
                'status': 'error',
                'available': False,
                'error': str(e),
                'error_type': 'unknown',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def check_multiple_protocols(
        self, 
        domain: str, 
        keyword: Optional[str] = None
    ) -> Dict:
        """
        同時檢查 HTTP 和 HTTPS
        
        Returns:
            {
                'https': {...},
                'http': {...},
                'best_result': {...}
            }
        """
        https_result = await self.check_uptime(domain, keyword, 'https')
        http_result = await self.check_uptime(domain, keyword, 'http')
        
        # 選擇最好的結果
        if https_result.get('available'):
            best_result = https_result
            best_protocol = 'https'
        elif http_result.get('available'):
            best_result = http_result
            best_protocol = 'http'
        else:
            best_result = https_result  # 都失敗就返回 https 的結果
            best_protocol = 'none'
        
        return {
            'https': https_result,
            'http': http_result,
            'best_result': best_result,
            'best_protocol': best_protocol,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def check_ssl_certificate(self, domain: str) -> Dict:
        """
        檢查 SSL 證書狀態
        
        Returns:
            {
                'status': 'success/error',
                'valid': bool,
                'expires_in_days': int,
                'issuer': str,
                'error': str (if error)
            }
        """
        try:
            import ssl
            import socket
            from datetime import datetime
            
            context = ssl.create_default_context()
            
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # 解析到期日
                    not_after = cert.get('notAfter')
                    if not_after:
                        expire_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                        days_left = (expire_date - datetime.utcnow()).days
                    else:
                        days_left = -1
                    
                    # 取得發行者
                    issuer = dict(x[0] for x in cert.get('issuer', []))
                    issuer_name = issuer.get('organizationName', 'Unknown')
                    
                    return {
                        'status': 'success',
                        'valid': days_left > 0,
                        'expires_in_days': days_left,
                        'issuer': issuer_name,
                        'not_after': not_after,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"SSL check failed for {domain}: {e}")
            return {
                'status': 'error',
                'valid': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

