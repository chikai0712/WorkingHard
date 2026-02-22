"""Alert decision engine - 決策引擎核心邏輯"""
from typing import Dict, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AlertDecisionEngine:
    """
    告警決策引擎
    輸入: 三層監控結果
    輸出: 根因分析 + 告警等級
    """
    
    def analyze(self, domain: str, checks: Dict) -> Optional[Dict]:
        """
        分析監控結果並產生告警決策
        
        Args:
            domain: 網域名稱
            checks: {
                'securitytrails': {'ns_changed': bool, 'whois_changed': bool, 'details': dict},
                'global_dns': {'resolved_ips': list, 'status': str},
                'isp_dns': {'failed_isps': list, 'success_rate': float, 'details': dict},
                'uptime': {'keyword_match': bool, 'http_status': int, 'available': bool}
            }
            
        Returns:
            Alert dict or None if no alert needed
        """
        
        # P0: NS 紀錄變動 (最高優先級 - 域名劫持)
        if checks.get('securitytrails', {}).get('ns_changed'):
            return self._create_alert(
                level='P0',
                root_cause='domain_hijacked',
                title='網域所有權遭劫持',
                description='Nameserver 已變更為非授權節點，這是最嚴重的安全事件',
                evidence={
                    'old_ns': checks['securitytrails'].get('old_ns', []),
                    'new_ns': checks['securitytrails'].get('new_ns', []),
                    'changed_at': checks['securitytrails'].get('changed_at')
                },
                recommendation='立即聯絡域名註冊商確認所有權，檢查帳號是否被入侵'
            )
        
        global_dns_ok = checks.get('global_dns', {}).get('status') == 'ok'
        isp_success_rate = checks.get('isp_dns', {}).get('success_rate', 1.0)
        
        # P1: ISP 污染 (全球正常但區域失敗)
        if global_dns_ok and isp_success_rate < 0.5:
            failed_isps = checks['isp_dns'].get('failed_isps', [])
            return self._create_alert(
                level='P1',
                root_cause='isp_blocked',
                title='區域性 ISP 封鎖或 DNS 污染',
                description=f'全球解析正常，但 {len(failed_isps)} 個 ISP 解析異常',
                evidence={
                    'global_dns': checks['global_dns'],
                    'failed_isps': failed_isps,
                    'success_rate': isp_success_rate
                },
                recommendation='聯絡當地代理商排查路徑，可能需要更換 CDN 節點或 IP'
            )
        
        # P1: 內容竄改 (DNS 正常但關鍵字不符)
        uptime_data = checks.get('uptime', {})
        if global_dns_ok and not uptime_data.get('keyword_match') and uptime_data.get('available'):
            return self._create_alert(
                level='P1',
                root_cause='content_defacement',
                title='網站內容被竄改',
                description='DNS 解析正常但網頁內容與預期不符，可能遭入侵',
                evidence={
                    'http_status': uptime_data.get('http_status'),
                    'keyword_expected': uptime_data.get('keyword_expected'),
                    'keyword_found': uptime_data.get('keyword_found', False)
                },
                recommendation='立即檢查主機安全性，查看是否有未授權的檔案修改'
            )
        
        # P2: 配置錯誤 (全部失敗)
        if not global_dns_ok:
            return self._create_alert(
                level='P2',
                root_cause='config_error',
                title='DNS 配置錯誤',
                description='全球解析失敗，可能是 DNS 配置問題',
                evidence={
                    'global_dns': checks['global_dns'],
                    'ns_records': checks.get('securitytrails', {}).get('current_ns', [])
                },
                recommendation='檢查 DNS 配置，確認 A 記錄和 NS 記錄是否正確'
            )
        
        # P2: WHOIS 異動 (非緊急但需關注)
        if checks.get('securitytrails', {}).get('whois_changed'):
            return self._create_alert(
                level='P2',
                root_cause='whois_changed',
                title='WHOIS 資訊變動',
                description='域名註冊資訊發生變更',
                evidence={
                    'changes': checks['securitytrails'].get('whois_changes', {})
                },
                recommendation='確認變更是否為授權操作，檢查到期日是否正確'
            )
        
        # 無異常
        return None
    
    def _create_alert(
        self,
        level: str,
        root_cause: str,
        title: str,
        description: str,
        evidence: Dict,
        recommendation: str
    ) -> Dict:
        """建立標準化的告警物件"""
        return {
            'alert_level': level,
            'root_cause': root_cause,
            'title': title,
            'description': description,
            'evidence': evidence,
            'recommendation': recommendation,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def format_alert_message(self, domain: str, alert: Dict) -> str:
        """
        格式化告警訊息為「人話報告」
        
        Args:
            domain: 網域名稱
            alert: 告警物件
            
        Returns:
            格式化的告警訊息
        """
        level_emoji = {
            'P0': '🚨',
            'P1': '⚠️',
            'P2': 'ℹ️'
        }
        
        emoji = level_emoji.get(alert['alert_level'], '📢')
        
        message = f"""
{emoji} **[網域異常報告 - {alert['alert_level']}]**

**影響網域**: `{domain}`
**事件性質**: {alert['title']}
**根本原因**: {alert['root_cause']}

**詳細說明**:
{alert['description']}

**證據資訊**:
```json
{self._format_evidence(alert['evidence'])}
```

**建議行動**:
{alert['recommendation']}

**發生時間**: {alert['timestamp']}
        """.strip()
        
        return message
    
    def _format_evidence(self, evidence: Dict, indent: int = 0) -> str:
        """格式化證據資訊"""
        import json
        return json.dumps(evidence, indent=2, ensure_ascii=False)

