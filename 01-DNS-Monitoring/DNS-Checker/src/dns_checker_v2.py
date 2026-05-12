#!/usr/bin/env python3
"""
DNS 域名解析檢查工具（改進版本）

改進內容：
1. 修復 IP 處理邏輯錯誤
2. 增強錯誤處理
3. 添加日誌記錄
4. 改進白名單處理（支援註釋、空行過濾）
5. 添加輸入驗證
6. 支援超時設置
"""

import argparse
import os
import sys
import logging
import ipaddress
from typing import List, Optional
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

class DNSChecker:
    """DNS 檢查器類"""
    
    def __init__(self, nameserver: str, timeout: int = DEFAULT_TIMEOUT):
        """
        初始化 DNS 檢查器
        
        Args:
            nameserver: DNS 伺服器 IP 地址
            timeout: 查詢超時時間（秒）
        """
        self.nameserver = nameserver
        self.timeout = timeout
        self.resolver = Resolver()
        self.resolver.nameservers = [nameserver]
        self.resolver.timeout = timeout
        self.resolver.lifetime = timeout
    
    def check_domain(self, record: str, whitelist: List[str]) -> tuple:
        """
        檢查域名解析結果是否在白名單中
        
        Args:
            record: 要檢查的域名
            whitelist: IP 白名單列表（CIDR 格式）
        
        Returns:
            tuple: (status, message, exit_code)
                status: 'OK', 'CRITICAL', 'UNKNOWN'
                message: 狀態消息
                exit_code: 退出碼（0=OK, 2=CRITICAL, 3=UNKNOWN）
        """
        try:
            logger.info(f"檢查域名: {record} (nameserver: {self.nameserver})")
            answers = self.resolver.resolve(record)
            
            resolved_ips = []
            critical_ips = []
            
            for answer in answers:
                ip = answer.address
                resolved_ips.append(ip)
                
                if not self.is_ip_in_whitelist(ip, whitelist):
                    critical_ips.append(ip)
                    logger.warning(f"IP {ip} 不在白名單中")
            
            if critical_ips:
                message = f"CRITICAL - {record} resolved to {', '.join(critical_ips)} (not in whitelist, nameserver: {self.nameserver})"
                logger.error(message)
                return ('CRITICAL', message, 2)
            
            message = f"OK - {record} resolved to {', '.join(resolved_ips)} (nameserver: {self.nameserver})"
            logger.info(message)
            return ('OK', message, 0)
            
        except NXDOMAIN:
            message = f"UNKNOWN - Domain {record} does not exist (nameserver: {self.nameserver})"
            logger.error(message)
            return ('UNKNOWN', message, 3)
            
        except NoAnswer:
            message = f"UNKNOWN - No answer for {record} (nameserver: {self.nameserver})"
            logger.error(message)
            return ('UNKNOWN', message, 3)
            
        except Timeout:
            message = f"UNKNOWN - DNS query timeout for {record} (nameserver: {self.nameserver})"
            logger.error(message)
            return ('UNKNOWN', message, 3)
            
        except DNSException as e:
            message = f"UNKNOWN - DNS error for {record}: {str(e)} (nameserver: {self.nameserver})"
            logger.error(message)
            return ('UNKNOWN', message, 3)
            
        except Exception as e:
            message = f"UNKNOWN - Unexpected error for {record}: {str(e)} (nameserver: {self.nameserver})"
            logger.error(message, exc_info=True)
            return ('UNKNOWN', message, 3)
    
    def is_ip_in_whitelist(self, ip: str, whitelist: List[str]) -> bool:
        """
        檢查 IP 是否在白名單中（修復版本）
        
        Args:
            ip: IP 地址（字符串）
            whitelist: IP 白名單列表（CIDR 格式）
        
        Returns:
            bool: True 如果 IP 在白名單中，False 否則
        """
        try:
            # 修復：使用 ip_address 處理單個 IP
            ip_addr = ipaddress.ip_address(ip)
        except ValueError:
            logger.warning(f"無效的 IP 地址: {ip}")
            return False
        
        for ip_range in whitelist:
            # 跳過空行和註釋
            ip_range = ip_range.strip()
            if not ip_range or ip_range.startswith('#'):
                continue
            
            try:
                # 修復：使用 in 運算符檢查 IP 是否在網絡內
                network = ipaddress.ip_network(ip_range, strict=False)
                if ip_addr in network:
                    logger.debug(f"IP {ip} 在白名單範圍 {ip_range} 中")
                    return True
            except ValueError:
                logger.warning(f"無效的白名單範圍: {ip_range}")
                continue
        
        return False

def load_whitelist(whitelist_path: str) -> List[str]:
    """
    載入白名單文件
    
    Args:
        whitelist_path: 白名單文件路徑
    
    Returns:
        List[str]: 白名單列表
    """
    if not os.path.isfile(whitelist_path):
        raise FileNotFoundError(f"白名單文件不存在: {whitelist_path}")
    
    whitelist = []
    with open(whitelist_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳過空行和註釋
            if line and not line.startswith('#'):
                whitelist.append(line)
    
    logger.info(f"載入白名單: {len(whitelist)} 個條目")
    return whitelist

def validate_nameserver(nameserver: str) -> bool:
    """
    驗證 nameserver IP 地址格式
    
    Args:
        nameserver: DNS 伺服器 IP 地址
    
    Returns:
        bool: True 如果格式正確，False 否則
    """
    try:
        ipaddress.ip_address(nameserver)
        return True
    except ValueError:
        return False

def main():
    parser = argparse.ArgumentParser(
        description='DNS 域名解析檢查工具（改進版本）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
退出碼：
  0 - OK: 所有 IP 都在白名單中
  2 - CRITICAL: 有 IP 不在白名單中
  3 - UNKNOWN: 發生錯誤

範例：
  %(prog)s -R example.com -S 8.8.8.8 -W whitelist.txt
  %(prog)s -R example.com -S 8.8.8.8 --whitelist-path /path/to/whitelist.txt
        """
    )
    
    parser.add_argument(
        '-R', '--record',
        required=True,
        help='要檢查的域名'
    )
    
    parser.add_argument(
        '-S', '--nameserver',
        required=True,
        help='DNS 伺服器 IP 地址'
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
        '-v', '--verbose',
        action='store_true',
        help='詳細輸出（DEBUG 級別日誌）'
    )
    
    args = parser.parse_args()
    
    # 設置日誌級別
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 驗證 nameserver
    if not validate_nameserver(args.nameserver):
        print(f"ERROR - 無效的 nameserver IP 地址: {args.nameserver}")
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
    
    # 檢查白名單是否為空
    if not whitelist:
        print(f"WARNING - 白名單為空: {whitelist_path}")
    
    # 執行檢查
    checker = DNSChecker(args.nameserver, args.timeout)
    status, message, exit_code = checker.check_domain(args.record, whitelist)
    
    print(message)
    sys.exit(exit_code)

if __name__ == '__main__':
    main()

