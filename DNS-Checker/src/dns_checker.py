#!/usr/bin/env python3
"""
DNS 域名解析檢查工具（原始版本）

功能：
- 檢查域名在指定 DNS 伺服器上的解析結果
- 驗證解析出的 IP 是否在白名單範圍內
- 支援 Nagios/Icinga 風格的退出碼
"""

import argparse
import os
import socket
import ipaddress
from dns.resolver import Resolver
import sys

DEFAULT_WHITELIST_PATH = '/opt/dnsapi/'

def check_domain(record, nameserver, whitelist):
    """
    檢查域名解析結果是否在白名單中
    
    Args:
        record: 要檢查的域名
        nameserver: DNS 伺服器 IP
        whitelist: IP 白名單列表（CIDR 格式）
    
    Returns:
        sys.exit(0): OK - 所有 IP 都在白名單中
        sys.exit(2): CRITICAL - 有 IP 不在白名單中
        sys.exit(3): UNKNOWN - 發生錯誤
    """
    try:
        resolver = Resolver()
        resolver.nameservers = [nameserver]
        answers = resolver.resolve(record)
        
        for answer in answers:
            ip = answer.address
            if not is_ip_in_whitelist(ip, whitelist):
                print(f"CRITICAL - {record} resolved to {ip} (nameserver: {nameserver})")
                sys.exit(2)  # Exit code 2 indicates CRITICAL
        
        print(f"OK - {record} resolved to {ip} (nameserver: {nameserver})")
        sys.exit(0)  # Exit code 0 indicates OK
        
    except Exception as e:
        print(f"UNKNOWN - Error: {str(e)}")
        sys.exit(3)  # Exit code 3 indicates UNKNOWN

def is_ip_in_whitelist(ip, whitelist):
    """
    檢查 IP 是否在白名單中
    
    Args:
        ip: IP 地址（字符串）
        whitelist: IP 白名單列表（CIDR 格式）
    
    Returns:
        bool: True 如果 IP 在白名單中，False 否則
    
    問題：
        - 將單個 IP 地址當作 IP 網絡處理，邏輯錯誤
        - 應該先將 IP 轉換為 IP 對象，然後檢查是否在白名單網絡中
    """
    try:
        ip_network = ipaddress.ip_network(ip)  # 問題：單個 IP 不能直接轉換為 network
    except ValueError:
        return False  # Not a valid IP, ignore it
    
    for ip_range in whitelist:
        try:
            if ip_network.overlaps(ipaddress.ip_network(ip_range)):
                return True
        except ValueError:
            pass  # Ignore invalid network ranges
    
    return False

def main():
    parser = argparse.ArgumentParser(description='Check domain resolution status.')
    parser.add_argument('-R', '--record', required=True, help='Domain name to check')
    parser.add_argument('-S', '--nameserver', required=True, help='DNS server to use')
    parser.add_argument('-W', '--whitelist', help='Whitelist filename (without path)')
    
    args = parser.parse_args()
    
    if args.whitelist:
        whitelist_path = os.path.join(DEFAULT_WHITELIST_PATH, args.whitelist)
    else:
        whitelist_path = os.path.join(DEFAULT_WHITELIST_PATH, 'whitelist.txt')
    
    if not os.path.isfile(whitelist_path):
        print(f"ERROR - Whitelist file not found: {whitelist_path}")
        sys.exit(3)  # Exit code 3 indicates UNKNOWN
    
    with open(whitelist_path, 'r') as f:
        whitelist = [line.strip() for line in f.readlines()]
    
    check_domain(args.record, args.nameserver, whitelist)

if __name__ == '__main__':
    main()

