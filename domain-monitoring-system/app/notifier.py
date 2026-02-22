"""Slack notification module"""
import httpx
from typing import Dict, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Slack 告警通知模組"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or settings.SLACK_WEBHOOK_URL
    
    async def send_alert(self, message: str, domain: str, alert_level: str) -> bool:
        """
        發送告警到 Slack
        
        Args:
            message: 告警訊息
            domain: 網域名稱
            alert_level: 告警等級 (P0/P1/P2)
            
        Returns:
            bool: 是否發送成功
        """
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False
        
        # 根據告警等級設定顏色
        color_map = {
            'P0': '#FF0000',  # 紅色
            'P1': '#FFA500',  # 橘色
            'P2': '#0000FF'   # 藍色
        }
        
        payload = {
            "attachments": [
                {
                    "color": color_map.get(alert_level, '#808080'),
                    "title": f"Domain Alert: {domain}",
                    "text": message,
                    "footer": "Domain Monitoring System",
                    "ts": int(datetime.utcnow().timestamp())
                }
            ]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Alert sent to Slack for domain: {domain}")
                    return True
                else:
                    logger.error(f"Failed to send Slack alert: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return False
    
    async def send_simple_message(self, text: str) -> bool:
        """發送簡單訊息"""
        if not self.webhook_url:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json={"text": text},
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
            return False


from datetime import datetime

