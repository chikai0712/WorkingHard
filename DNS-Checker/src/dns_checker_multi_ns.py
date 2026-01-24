#!/usr/bin/env python3
"""
DNS 域名解析檢查工具（多 NS 版本）

功能：
- 使用多個 ISP 的 NS 檢測域名解析是否異常
- 比較不同 NS 的解析結果，檢測 DNS 劫持或污染
- 支援白名單驗證
- 生成詳細的檢測報告
"""

import argparse
import os
import sys
import logging
import ipaddress
from typing import List, Dict, Tuple, Set
from collections import defaultdict
from dns.resolver import Resolver, NXDOMAIN, NoAnswer, Timeout
from dns.exception import DNSException

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_WHITELIST_PATH = '/opt/dnsapi/'
DEFAULT_TIMEOUT = 5  # 秒

# 預設的多個 ISP NS 列表
DEFAULT_NAMESERVERS = [
    '8.8.8.8',      # Google DNS
    '8.8.4.4',      # Google DNS
    '1.1.1.1',      # Cloudflare DNS
    '1.0.0.1',      # Cloudflare DNS
    '208.67.222.222',  # OpenDNS
    '208.67.220.220',  # OpenDNS
    '9.9.9.9',      # Quad9
    '149.112.112.112',  # Quad9
]

class MultiNSDNSChecker:
    """多 NS DNS 檢查器類"""
    
    def __init__(self, nameservers: List[str], timeout: int = DEFAULT_TIMEOUT):
        """
        初始化多 NS DNS 檢查器
        
        Args:
            nameservers: DNS 伺服器 IP 地址列表
            timeout: 查詢超時時間（秒）
        """
        self.nameservers = nameservers
        self.timeout = timeout
        self.resolvers = {}
        
        # 為每個 nameserver 創建 resolver
        for ns in nameservers:
            resolver = Resolver()
            resolver.nameservers = [ns]
            resolver.timeout = timeout
            resolver.lifetime = timeout
            self.resolvers[ns] = resolver
    
    def check_domain_multi_ns(self, record: str, whitelist: List[str]) -> Dict:
        """
        使用多個 NS 檢查域名解析
        
        Args:
            record: 要檢查的域名
            whitelist: IP 白名單列表（CIDR 格式）
        
        Returns:
            dict: 檢測結果
                {
                    'domain': record,
                    'results': {
                        'nameserver': {
                            'status': 'OK'|'CRITICAL'|'UNKNOWN',
                            'ips': [...],
                            'message': '...',
                            'in_whitelist': bool
                        }
                    },
                    'summary': {
                        'total_ns': int,
                        'successful_ns': int,
                        'failed_ns': int,
                        'consistent': bool,
                        'all_in_whitelist': bool,
                        'anomaly_detected': bool
                    }
                }
        """
        results = {}
        all_ips = set()
        ns_ip_map = defaultdict(set)  # nameserver -> set of IPs
        
        logger.info(f"開始檢查域名: {record} (使用 {len(self.nameservers)} 個 NS)")
        
        # 檢查每個 nameserver
        for nameserver in self.nameservers:
            try:
                resolver = self.resolvers[nameserver]
                answers = resolver.resolve(record)
                
                ips = [answer.address for answer in answers]
                all_ips.update(ips)
                ns_ip_map[nameserver] = set(ips)
                
                # 檢查 IP 是否在白名單中
                in_whitelist = all(self.is_ip_in_whitelist(ip, whitelist) for ip in ips)
                
                if in_whitelist:
                    status = 'OK'
                    message = f"OK - {record} resolved to {', '.join(ips)} (nameserver: {nameserver})"
                else:
                    status = 'CRITICAL'
                    invalid_ips = [ip for ip in ips if not self.is_ip_in_whitelist(ip, whitelist)]
                    message = f"CRITICAL - {record} resolved to {', '.join(invalid_ips)} (not in whitelist, nameserver: {nameserver})"
                
                results[nameserver] = {
                    'status': status,
                    'ips': ips,
                    'message': message,
                    'in_whitelist': in_whitelist
                }
                
                logger.info(f"  {nameserver}: {status} - {', '.join(ips)}")
                
            except NXDOMAIN:
                results[nameserver] = {
                    'status': 'UNKNOWN',
                    'ips': [],
                    'message': f"UNKNOWN - Domain {record} does not exist (nameserver: {nameserver})",
                    'in_whitelist': False
                }
                logger.warning(f"  {nameserver}: Domain does not exist")
                
            except (NoAnswer, Timeout, DNSException) as e:
                results[nameserver] = {
                    'status': 'UNKNOWN',
                    'ips': [],
                    'message': f"UNKNOWN - DNS error for {record}: {str(e)} (nameserver: {nameserver})",
                    'in_whitelist': False
                }
                logger.warning(f"  {nameserver}: DNS error - {str(e)}")
                
            except Exception as e:
                results[nameserver] = {
                    'status': 'UNKNOWN',
                    'ips': [],
                    'message': f"UNKNOWN - Unexpected error: {str(e)} (nameserver: {nameserver})",
                    'in_whitelist': False
                }
                logger.error(f"  {nameserver}: Unexpected error - {str(e)}", exc_info=True)
        
        # 分析結果
        summary = self._analyze_results(results, ns_ip_map, whitelist)
        
        return {
            'domain': record,
            'results': results,
            'summary': summary
        }
    
    def _analyze_results(self, results: Dict, ns_ip_map: Dict, whitelist: List[str]) -> Dict:
        """
        分析多 NS 檢測結果
        
        Args:
            results: 各 NS 的檢測結果
            ns_ip_map: nameserver -> IP set 映射
            whitelist: IP 白名單
        
        Returns:
            dict: 分析摘要
        """
        total_ns = len(self.nameservers)
        successful_ns = sum(1 for r in results.values() if r['status'] == 'OK')
        failed_ns = sum(1 for r in results.values() if r['status'] == 'CRITICAL')
        unknown_ns = sum(1 for r in results.values() if r['status'] == 'UNKNOWN')
        
        # 檢查所有成功的 NS 是否解析到相同的 IP
        successful_results = {ns: r for ns, r in results.items() if r['status'] == 'OK'}
        if len(successful_results) > 1:
            # 獲取第一個成功的 NS 的 IP 集合作為基準
            first_ns = list(successful_results.keys())[0]
            baseline_ips = ns_ip_map[first_ns]
            
            # 檢查其他 NS 是否解析到相同的 IP
            consistent = all(
                ns_ip_map[ns] == baseline_ips 
                for ns in successful_results.keys()
            )
        else:
            consistent = True  # 只有一個或沒有成功的 NS，視為一致
        
        # 檢查所有 IP 是否都在白名單中
        all_ips = set()
        for r in results.values():
            all_ips.update(r['ips'])
        
        all_in_whitelist = all(
            self.is_ip_in_whitelist(ip, whitelist) 
            for ip in all_ips
        )
        
        # 檢測異常
        # 異常情況：
        # 1. 有 NS 解析到不在白名單中的 IP
        # 2. 不同 NS 解析到不同的 IP（不一致）
        # 3. 部分 NS 解析失敗（可能是 DNS 污染）
        anomaly_detected = (
            not all_in_whitelist or  # 有 IP 不在白名單中
            not consistent or  # 不同 NS 解析結果不一致
            (unknown_ns > 0 and successful_ns > 0)  # 部分 NS 失敗，部分成功（可能是污染）
        )
        
        return {
            'total_ns': total_ns,
            'successful_ns': successful_ns,
            'failed_ns': failed_ns,
            'unknown_ns': unknown_ns,
            'consistent': consistent,
            'all_in_whitelist': all_in_whitelist,
            'anomaly_detected': anomaly_detected,
            'unique_ips': sorted(all_ips),
            'ip_distribution': {
                ns: sorted(ips) 
                for ns, ips in ns_ip_map.items()
            }
        }
    
    def is_ip_in_whitelist(self, ip: str, whitelist: List[str]) -> bool:
        """
        檢查 IP 是否在白名單中
        
        Args:
            ip: IP 地址（字符串）
            whitelist: IP 白名單列表（CIDR 格式）
        
        Returns:
            bool: True 如果 IP 在白名單中，False 否則
        """
        try:
            ip_addr = ipaddress.ip_address(ip)
        except ValueError:
            logger.warning(f"無效的 IP 地址: {ip}")
            return False
        
        for ip_range in whitelist:
            ip_range = ip_range.strip()
            if not ip_range or ip_range.startswith('#'):
                continue
            
            try:
                network = ipaddress.ip_network(ip_range, strict=False)
                if ip_addr in network:
                    return True
            except ValueError:
                logger.warning(f"無效的白名單範圍: {ip_range}")
                continue
        
        return False
    
    def generate_report(self, check_result: Dict, format: str = 'text') -> str:
        """
        生成檢測報告
        
        Args:
            check_result: 檢測結果
            format: 報告格式 ('text', 'json', 'nagios')
        
        Returns:
            str: 報告內容
        """
        if format == 'json':
            import json
            return json.dumps(check_result, indent=2, ensure_ascii=False)
        
        elif format == 'nagios':
            summary = check_result['summary']
            if summary['anomaly_detected']:
                if not summary['all_in_whitelist']:
                    return f"CRITICAL - Domain {check_result['domain']} has IPs not in whitelist"
                elif not summary['consistent']:
                    return f"CRITICAL - Domain {check_result['domain']} resolved to different IPs across nameservers"
                else:
                    return f"WARNING - Domain {check_result['domain']} has partial DNS failures"
            else:
                return f"OK - Domain {check_result['domain']} resolved consistently across all nameservers"
        
        else:  # text
            lines = []
            lines.append("=" * 80)
            lines.append(f"DNS 檢測報告: {check_result['domain']}")
            lines.append("=" * 80)
            lines.append("")
            
            # 摘要
            summary = check_result['summary']
            lines.append("📊 檢測摘要:")
            lines.append(f"  總 NS 數量: {summary['total_ns']}")
            lines.append(f"  成功: {summary['successful_ns']}")
            lines.append(f"  失敗: {summary['failed_ns']}")
            lines.append(f"  未知: {summary['unknown_ns']}")
            lines.append(f"  解析一致性: {'✅ 一致' if summary['consistent'] else '❌ 不一致'}")
            lines.append(f"  白名單驗證: {'✅ 全部通過' if summary['all_in_whitelist'] else '❌ 有 IP 未通過'}")
            lines.append(f"  異常檢測: {'⚠️  檢測到異常' if summary['anomaly_detected'] else '✅ 正常'}")
            lines.append("")
            
            # 各 NS 結果
            lines.append("🔍 各 NS 檢測結果:")
            for nameserver, result in check_result['results'].items():
                status_icon = {
                    'OK': '✅',
                    'CRITICAL': '❌',
                    'UNKNOWN': '⚠️'
                }.get(result['status'], '❓')
                
                lines.append(f"  {status_icon} {nameserver}:")
                if result['ips']:
                    lines.append(f"    IP: {', '.join(result['ips'])}")
                    lines.append(f"    白名單: {'✅' if result['in_whitelist'] else '❌'}")
                lines.append(f"    狀態: {result['status']}")
                lines.append(f"    訊息: {result['message']}")
                lines.append("")
            
            # IP 分布
            if summary['ip_distribution']:
                lines.append("📈 IP 分布:")
                for ns, ips in summary['ip_distribution'].items():
                    lines.append(f"  {ns}: {', '.join(ips)}")
                lines.append("")
            
            # 異常分析
            if summary['anomaly_detected']:
                lines.append("⚠️  異常分析:")
                if not summary['all_in_whitelist']:
                    invalid_ips = [
                        ip for ip in summary['unique_ips']
                        if not self.is_ip_in_whitelist(ip, [])  # 需要傳入實際 whitelist
                    ]
                    lines.append(f"  - 發現不在白名單中的 IP: {', '.join(invalid_ips)}")
                
                if not summary['consistent']:
                    lines.append("  - 不同 NS 解析到不同的 IP，可能存在 DNS 劫持或污染")
                
                if summary['unknown_ns'] > 0 and summary['successful_ns'] > 0:
                    lines.append(f"  - {summary['unknown_ns']} 個 NS 解析失敗，可能存在 DNS 污染")
                lines.append("")
            
            lines.append("=" * 80)
            return "\n".join(lines)

def load_whitelist(whitelist_path: str) -> List[str]:
    """載入白名單文件"""
    if not os.path.isfile(whitelist_path):
        raise FileNotFoundError(f"白名單文件不存在: {whitelist_path}")
    
    whitelist = []
    with open(whitelist_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                whitelist.append(line)
    
    logger.info(f"載入白名單: {len(whitelist)} 個條目")
    return whitelist

def validate_nameserver(nameserver: str) -> bool:
    """驗證 nameserver IP 地址格式"""
    try:
        ipaddress.ip_address(nameserver)
        return True
    except ValueError:
        return False

def main():
    parser = argparse.ArgumentParser(
        description='DNS 域名解析檢查工具（多 NS 版本）- 檢測域名異常',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
功能說明：
  使用多個 ISP 的 NS 檢測域名解析是否異常，包括：
  - DNS 劫持檢測（解析到非預期 IP）
  - DNS 污染檢測（部分 NS 解析失敗）
  - 解析一致性檢測（不同 NS 解析結果是否一致）

退出碼：
  0 - OK: 所有 NS 解析一致且都在白名單中
  2 - CRITICAL: 檢測到異常（IP 不在白名單或解析不一致）
  3 - UNKNOWN: 發生錯誤

範例：
  %(prog)s -R example.com -W whitelist.txt
  %(prog)s -R example.com -S 8.8.8.8,1.1.1.1,9.9.9.9 -W whitelist.txt
  %(prog)s -R example.com --format json
        """
    )
    
    parser.add_argument(
        '-R', '--record',
        required=True,
        help='要檢查的域名'
    )
    
    parser.add_argument(
        '-S', '--nameservers',
        help='DNS 伺服器 IP 地址列表（逗號分隔），默認使用多個公共 DNS'
    )
    
    parser.add_argument(
        '-W', '--whitelist',
        help='白名單文件名（相對於默認路徑）'
    )
    
    parser.add_argument(
        '--whitelist-path',
        help='白名單文件完整路徑（覆蓋 -W 選項）'
    )
    
    parser.add_argument(
        '--whitelist-dir',
        default=DEFAULT_WHITELIST_PATH,
        help=f'白名單文件目錄（默認: {DEFAULT_WHITELIST_PATH}）'
    )
    
    parser.add_argument(
        '-t', '--timeout',
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f'DNS 查詢超時時間（秒，默認: {DEFAULT_TIMEOUT}）'
    )
    
    parser.add_argument(
        '--format',
        choices=['text', 'json', 'nagios'],
        default='text',
        help='輸出格式（默認: text）'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='詳細輸出（DEBUG 級別日誌）'
    )
    
    args = parser.parse_args()
    
    # 設置日誌級別
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 確定 nameservers
    if args.nameservers:
        nameservers = [ns.strip() for ns in args.nameservers.split(',')]
    else:
        nameservers = DEFAULT_NAMESERVERS
    
    # 驗證 nameservers
    invalid_ns = [ns for ns in nameservers if not validate_nameserver(ns)]
    if invalid_ns:
        print(f"ERROR - 無效的 nameserver IP 地址: {', '.join(invalid_ns)}")
        sys.exit(3)
    
    # 確定白名單路徑
    if args.whitelist_path:
        whitelist_path = args.whitelist_path
    elif args.whitelist:
        whitelist_path = os.path.join(args.whitelist_dir, args.whitelist)
    else:
        whitelist_path = os.path.join(args.whitelist_dir, 'whitelist.txt')
    
    # 載入白名單
    try:
        whitelist = load_whitelist(whitelist_path)
    except FileNotFoundError as e:
        print(f"ERROR - {str(e)}")
        sys.exit(3)
    except Exception as e:
        print(f"ERROR - 載入白名單失敗: {str(e)}")
        sys.exit(3)
    
    # 執行檢查
    checker = MultiNSDNSChecker(nameservers, args.timeout)
    check_result = checker.check_domain_multi_ns(args.record, whitelist)
    
    # 生成報告
    report = checker.generate_report(check_result, args.format)
    print(report)
    
    # 根據結果設置退出碼
    summary = check_result['summary']
    if summary['anomaly_detected']:
        sys.exit(2)  # CRITICAL
    elif summary['unknown_ns'] == len(nameservers):
        sys.exit(3)  # UNKNOWN - 所有 NS 都失敗
    else:
        sys.exit(0)  # OK

if __name__ == '__main__':
    main()

