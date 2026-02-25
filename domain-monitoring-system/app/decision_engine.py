"""Alert decision engine - 決策引擎核心邏輯"""
from typing import Dict, Optional, List
from datetime import datetime
import logging

from app.timezone_utils import local_now

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
                'global_dns': {'resolved_ips': list, 'status': str, 'resolution_rate': float, 'whitelist_match_rate': float},
                'isp_dns': {'failed_isps': list, 'success_rate': float, 'resolution_rate': float, 'whitelist_match_rate': float, 'has_whitelist': bool, 'details': dict},
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
        isp_data = checks.get('isp_dns', {})
        resolution_rate = isp_data.get('resolution_rate', 1.0)
        whitelist_match_rate = isp_data.get('whitelist_match_rate', 1.0)
        has_whitelist = isp_data.get('has_whitelist', False)
        blocked_countries = isp_data.get('blocked_countries', [])
        country_results = isp_data.get('country_results', {})
        
        # 使用適當的成功率指標
        effective_success_rate = whitelist_match_rate if has_whitelist else resolution_rate
        
        # P1: 特定國家被阻擋 (新增：地區性封鎖檢測)
        if blocked_countries:
            blocked_country_names = {
                'VN': '越南',
                'ID': '印尼',
                'TW': '台灣',
                'US': '美國',
                'CN': '中國'
            }
            
            blocked_list = [
                f"{blocked_country_names.get(c['country_code'], c['country_code'])} (成功率: {c['success_rate']:.1%})"
                for c in blocked_countries
            ]
            
            return self._create_alert(
                level='P1',
                root_cause='country_blocked',
                title=f'特定國家 DNS 被阻擋',
                description=f'檢測到 {len(blocked_countries)} 個國家的 DNS 解析失敗或被阻擋',
                evidence={
                    'blocked_countries': blocked_countries,
                    'blocked_list': blocked_list,
                    'country_results': country_results,
                    'overall_success_rate': isp_data.get('success_rate', 0)
                },
                recommendation=f'受影響國家: {", ".join(blocked_list)}。建議聯絡當地代理商排查，可能需要更換 CDN 節點或使用備用域名'
            )
        
        # P1: ISP 污染 (全球正常但區域失敗)
        if global_dns_ok and effective_success_rate < 0.5:
            failed_isps = isp_data.get('failed_isps', [])
            
            # 過濾出真正的錯誤（排除白名單警告）
            critical_failures = [
                ns for ns in failed_isps 
                if ns.get('severity') == 'error'
            ]
            
            # 如果有真正的 DNS 錯誤才告警
            if critical_failures:
                return self._create_alert(
                    level='P1',
                    root_cause='isp_blocked',
                    title='區域性 ISP 封鎖或 DNS 污染',
                    description=f'全球解析正常，但 {len(critical_failures)} 個 DNS 伺服器解析失敗',
                    evidence={
                        'global_dns': checks['global_dns'],
                        'failed_dns_servers': critical_failures[:5],  # 最多顯示 5 個
                        'resolution_rate': resolution_rate,
                        'whitelist_match_rate': whitelist_match_rate
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
            failed_ns = isp_data.get('failed_nameservers', [])
            
            # 只統計真正的 DNS 錯誤
            critical_failures = [
                ns for ns in failed_ns 
                if ns.get('severity') == 'error'
            ]
            
            # 檢查是否所有 DNS 都無法解析（真正的配置錯誤）
            all_dns_errors = all(
                'Could not contact DNS servers' in ns.get('error', '') or 
                'NXDOMAIN' in ns.get('error', '') or
                'timeout' in ns.get('error', '').lower()
                for ns in critical_failures
            ) if critical_failures else False
            
            # 只有在真正無法解析時才產生告警
            if all_dns_errors and resolution_rate == 0:
                return self._create_alert(
                    level='P2',
                    root_cause='config_error',
                    title='DNS 配置錯誤',
                    description='所有 DNS 伺服器都無法解析此網域',
                    evidence={
                        'global_dns': checks['global_dns'],
                        'failed_nameservers': critical_failures[:3],  # 只顯示前 3 個
                        'resolution_rate': resolution_rate
                    },
                    recommendation='檢查網域是否已註冊，確認 DNS 記錄是否正確配置'
                )
        
        # P3: 白名單不匹配警告（可選）
        if has_whitelist and resolution_rate >= 0.5 and whitelist_match_rate < 0.3:
            warning_resolutions = [
                ns for ns in failed_ns 
                if ns.get('severity') == 'warning'
            ]
            
            if warning_resolutions:
                return self._create_alert(
                    level='P3',
                    root_cause='whitelist_mismatch',
                    title='IP 白名單不匹配',
                    description=f'DNS 解析正常，但 {len(warning_resolutions)} 個解析結果不在白名單內',
                    evidence={
                        'resolution_rate': resolution_rate,
                        'whitelist_match_rate': whitelist_match_rate,
                        'mismatched_resolutions': warning_resolutions[:3]
                    },
                    recommendation='檢查白名單設定是否正確，或更新預期的 IP 列表'
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
            'timestamp': local_now().isoformat()
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
            'P2': 'ℹ️',
            'P3': '💡'
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

