#!/usr/bin/env python3
"""
DNS 檢查工具單元測試
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
import ipaddress

# 添加 src 目錄到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dns_checker_v2 import DNSChecker, load_whitelist, validate_nameserver

class TestDNSChecker(unittest.TestCase):
    """DNS 檢查器測試類"""
    
    def setUp(self):
        """設置測試環境"""
        self.checker = DNSChecker('8.8.8.8')
        self.whitelist = [
            '192.168.1.0/24',
            '10.0.0.0/8',
            '172.16.0.0/12'
        ]
    
    def test_is_ip_in_whitelist_valid_ip(self):
        """測試有效的 IP 地址檢查"""
        # IP 在白名單中
        self.assertTrue(self.checker.is_ip_in_whitelist('192.168.1.100', self.whitelist))
        self.assertTrue(self.checker.is_ip_in_whitelist('10.0.0.1', self.whitelist))
        self.assertTrue(self.checker.is_ip_in_whitelist('172.16.0.1', self.whitelist))
        
        # IP 不在白名單中
        self.assertFalse(self.checker.is_ip_in_whitelist('203.0.113.1', self.whitelist))
        self.assertFalse(self.checker.is_ip_in_whitelist('8.8.8.8', self.whitelist))
    
    def test_is_ip_in_whitelist_invalid_ip(self):
        """測試無效的 IP 地址"""
        self.assertFalse(self.checker.is_ip_in_whitelist('invalid-ip', self.whitelist))
        self.assertFalse(self.checker.is_ip_in_whitelist('', self.whitelist))
    
    def test_is_ip_in_whitelist_with_comments(self):
        """測試白名單中的註釋"""
        whitelist_with_comments = [
            '# 這是註釋',
            '192.168.1.0/24',
            '',  # 空行
            '10.0.0.0/8'
        ]
        self.assertTrue(self.checker.is_ip_in_whitelist('192.168.1.100', whitelist_with_comments))
        self.assertFalse(self.checker.is_ip_in_whitelist('8.8.8.8', whitelist_with_comments))
    
    def test_is_ip_in_whitelist_invalid_network(self):
        """測試無效的網絡範圍"""
        whitelist_invalid = [
            '192.168.1.0/24',
            'invalid-network',
            '10.0.0.0/8'
        ]
        # 應該跳過無效的網絡範圍，繼續檢查
        self.assertTrue(self.checker.is_ip_in_whitelist('10.0.0.1', whitelist_invalid))
    
    @patch('dns_checker_v2.Resolver')
    def test_check_domain_ok(self, mock_resolver_class):
        """測試域名檢查 - OK 情況"""
        # 模擬 DNS 解析結果
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver
        
        mock_answer = MagicMock()
        mock_answer.address = '192.168.1.100'
        mock_resolver.resolve.return_value = [mock_answer]
        
        checker = DNSChecker('8.8.8.8')
        status, message, exit_code = checker.check_domain('example.com', self.whitelist)
        
        self.assertEqual(status, 'OK')
        self.assertEqual(exit_code, 0)
        self.assertIn('OK', message)
    
    @patch('dns_checker_v2.Resolver')
    def test_check_domain_critical(self, mock_resolver_class):
        """測試域名檢查 - CRITICAL 情況"""
        # 模擬 DNS 解析結果（IP 不在白名單中）
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver
        
        mock_answer = MagicMock()
        mock_answer.address = '203.0.113.1'  # 不在白名單中
        mock_resolver.resolve.return_value = [mock_answer]
        
        checker = DNSChecker('8.8.8.8')
        status, message, exit_code = checker.check_domain('example.com', self.whitelist)
        
        self.assertEqual(status, 'CRITICAL')
        self.assertEqual(exit_code, 2)
        self.assertIn('CRITICAL', message)
    
    @patch('dns_checker_v2.Resolver')
    def test_check_domain_multiple_ips(self, mock_resolver_class):
        """測試域名解析到多個 IP"""
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver
        
        mock_answer1 = MagicMock()
        mock_answer1.address = '192.168.1.100'
        mock_answer2 = MagicMock()
        mock_answer2.address = '203.0.113.1'  # 不在白名單中
        
        mock_resolver.resolve.return_value = [mock_answer1, mock_answer2]
        
        checker = DNSChecker('8.8.8.8')
        status, message, exit_code = checker.check_domain('example.com', self.whitelist)
        
        self.assertEqual(status, 'CRITICAL')
        self.assertEqual(exit_code, 2)

class TestUtils(unittest.TestCase):
    """工具函數測試類"""
    
    def test_validate_nameserver_valid(self):
        """測試有效的 nameserver IP"""
        self.assertTrue(validate_nameserver('8.8.8.8'))
        self.assertTrue(validate_nameserver('192.168.1.1'))
        self.assertTrue(validate_nameserver('2001:db8::1'))  # IPv6
    
    def test_validate_nameserver_invalid(self):
        """測試無效的 nameserver IP"""
        self.assertFalse(validate_nameserver('invalid'))
        self.assertFalse(validate_nameserver('999.999.999.999'))
        self.assertFalse(validate_nameserver(''))
    
    def test_load_whitelist(self):
        """測試載入白名單"""
        import tempfile
        
        # 創建臨時白名單文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('# 這是註釋\n')
            f.write('192.168.1.0/24\n')
            f.write('\n')  # 空行
            f.write('10.0.0.0/8\n')
            temp_path = f.name
        
        try:
            whitelist = load_whitelist(temp_path)
            self.assertEqual(len(whitelist), 2)
            self.assertIn('192.168.1.0/24', whitelist)
            self.assertIn('10.0.0.0/8', whitelist)
        finally:
            os.unlink(temp_path)
    
    def test_load_whitelist_not_found(self):
        """測試白名單文件不存在"""
        with self.assertRaises(FileNotFoundError):
            load_whitelist('/nonexistent/file.txt')

if __name__ == '__main__':
    unittest.main()

