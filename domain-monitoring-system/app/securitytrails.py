"""SecurityTrails API integration for NS and WHOIS monitoring"""
import os
import aiohttp
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SecurityTrailsChecker:
    """SecurityTrails API 客戶端"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('SECURITYTRAILS_API_KEY')
        self.base_url = 'https://api.securitytrails.com/v1'
        
    async def check_ns_records(self, domain: str) -> Dict:
        """
        檢查域名的 NS 記錄
        
        Returns:
            {
                'status': 'success/error',
                'current_ns': ['ns1.example.com', ...],
                'ns_changed': bool,
                'last_change': datetime or None
            }
        """
        if not self.api_key:
            logger.warning("SecurityTrails API key not configured")
            return {
                'status': 'error',
                'error': 'API key not configured',
                'ns_changed': False
            }
        
        try:
            headers = {
                'APIKEY': self.api_key,
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                # Get current DNS records
                url = f"{self.base_url}/domain/{domain}"
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"SecurityTrails API error: {response.status}")
                        return {
                            'status': 'error',
                            'error': f'API returned {response.status}',
                            'ns_changed': False
                        }
                    
                    data = await response.json()
                    current_ns = data.get('current_dns', {}).get('ns', {}).get('values', [])
                    
                    # Get NS history
                    history_url = f"{self.base_url}/history/{domain}/dns/ns"
                    async with session.get(history_url, headers=headers) as hist_response:
                        if hist_response.status == 200:
                            hist_data = await hist_response.json()
                            records = hist_data.get('records', [])
                            
                            # Check if NS changed recently (within 7 days)
                            ns_changed = False
                            last_change = None
                            
                            if len(records) > 1:
                                latest = records[0]
                                previous = records[1]
                                
                                if latest.get('values') != previous.get('values'):
                                    last_change = latest.get('last_seen')
                                    # Check if change is recent
                                    if last_change:
                                        change_date = datetime.fromisoformat(last_change.replace('Z', '+00:00'))
                                        days_ago = (datetime.utcnow() - change_date.replace(tzinfo=None)).days
                                        if days_ago <= 7:
                                            ns_changed = True
                            
                            return {
                                'status': 'success',
                                'current_ns': current_ns,
                                'ns_changed': ns_changed,
                                'last_change': last_change,
                                'history': records[:3]  # Keep last 3 records
                            }
                        else:
                            return {
                                'status': 'success',
                                'current_ns': current_ns,
                                'ns_changed': False,
                                'last_change': None
                            }
        
        except Exception as e:
            logger.error(f"SecurityTrails check failed for {domain}: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'ns_changed': False
            }
    
    async def check_whois(self, domain: str) -> Dict:
        """
        檢查 WHOIS 資訊
        
        Returns:
            {
                'status': 'success/error',
                'registrar': str,
                'created_date': str,
                'expires_date': str,
                'whois_changed': bool
            }
        """
        if not self.api_key:
            return {
                'status': 'error',
                'error': 'API key not configured',
                'whois_changed': False
            }
        
        try:
            headers = {
                'APIKEY': self.api_key,
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/domain/{domain}/whois"
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        return {
                            'status': 'error',
                            'error': f'API returned {response.status}',
                            'whois_changed': False
                        }
                    
                    data = await response.json()
                    
                    return {
                        'status': 'success',
                        'registrar': data.get('registrar'),
                        'created_date': data.get('createdDate'),
                        'expires_date': data.get('expiresDate'),
                        'whois_changed': False  # TODO: Implement change detection
                    }
        
        except Exception as e:
            logger.error(f"WHOIS check failed for {domain}: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'whois_changed': False
            }
