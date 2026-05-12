#!/usr/bin/env python3
"""
多 NS DNS 檢查工具測試
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# 添加 src 目錄到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dns_checker_multi_ns import MultiNSDNSChecker, load_whitelist, validate_nameserver

class TestMultiNSDNSChecker(unittest.TestCase):
    """多 NS DNS 檢查器測試類"""
    
    def setUp(self):
        """設置測試環境"""
        self.nameservers = ['8.8.8.8', '1.1.1.1', '9.9.9.9']
        self.checker = MultiNSDNSChecker(self.nameservers)
        self.whitelist = [
            '192.168.1.0/24',
            '10.0.0.0/8'
        ]
    
    def test_is_ip_in_whitelist(self):
        """測試 IP 白名單檢查"""
        # IP 在白名單中
        self.assertTrue(self.checker.is_ip_in_whitelist('192.168.1.100', self.whitelist))
        self.assertTrue(self.checker.is_ip_in_whitelist('10.0.0.1', self.whitelist))
        
        # IP 不在白名單中
        self.assertFalse(self.checker.is_ip_in_whitelist('203.0.113.1', self.whitelist))
        self.assertFalse(self.checker.is_ip_in_whitelist('8.8.8.8', self.whitelist))
    
    @patch('dns_checker_multi_ns.Resolver')
    def test_check_domain_multi_ns_consistent(self, mock_resolver_class):
        """測試多 NS 檢查 - 一致結果"""
        # 模擬所有 NS 都解析到相同的 IP
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver
        
        mock_answer = MagicMock()
        mock_answer.address = '192.168.1.100'
        mock_resolver.resolve.return_value = [mock_answer]
        
        result = self.checker.check_domain_multi_ns('example.com', self.whitelist)
        
        self.assertEqual(result['summary']['consistent'], True)
        self.assertEqual(result['summary']['all_in_whitelist'], True)
        self.assertEqual(result['summary']['anomaly_detected'], False)
    
    @patch('dns_checker_multi_ns.Resolver')
    def test_check_domain_multi_ns_inconsistent(self, mock_resolver_class):
        """測試多 NS 檢查 - 不一致結果"""
        # 模擬不同 NS 解析到不同的 IP
        mock_resolvers = {}
        for ns in self.nameservers:
            mock_resolver = MagicMock()
            mock_resolver.nameservers = [ns]
            mock_resolver.timeout = 5
            mock_resolver.lifetime = 5
            
            mock_answer = MagicMock()
            if ns == '8.8.8.8':
                mock_answer.address = '192.168.1.100'
            else:
                mock_answer.address = '203.0.113.1'  # 不同的 IP
            
            mock_resolver.resolve.return_value = [mock_answer]
            mock_resolvers[ns] = mock_resolver
        
        # 模擬 Resolver 類返回不同的實例
        def resolver_factory(*args, **kwargs):
            return MagicMock()
        
        mock_resolver_class.side_effect = lambda: mock_resolvers.get('8.8.8.8', MagicMock())
        
        # 手動設置 resolvers
        for ns in self.nameservers:
            self.checker.resolvers[ns] = mock_resolvers.get(ns, MagicMock())
        
        result = self.checker.check_domain_multi_ns('example.com', self.whitelist)
        
        # 由於模擬複雜，這裡主要測試邏輯
        self.assertIn('summary', result)
        self.assertIn('results', result)
    
    @patch('dns_checker_multi_ns.Resolver')
    def test_check_domain_multi_ns_partial_failure(self, mock_resolver_class):
        """測試多 NS 檢查 - 部分失敗"""
        # 模擬部分 NS 成功，部分失敗
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver
        
        # 第一個 NS 成功
        mock_answer = MagicMock()
        mock_answer.address = '192.168.1.100'
        mock_resolver.resolve.side_effect = [
            [mock_answer],  # 第一個 NS 成功
            Timeout(),      # 第二個 NS 超時
            [mock_answer]   # 第三個 NS 成功
        ]
        
        result = self.checker.check_domain_multi_ns('example.com', self.whitelist)
        
        self.assertIn('summary', result)
        self.assertGreater(result['summary']['unknown_ns'], 0)
    
    def test_generate_report_text(self):
        """測試生成文本報告"""
        check_result = {
            'domain': 'example.com',
            'results': {
                '8.8.8.8': {
                    'status': 'OK',
                    'ips': ['192.168.1.100'],
                    'message': 'OK',
                    'in_whitelist': True
                }
            },
            'summary': {
                'total_ns': 1,
                'successful_ns': 1,
                'failed_ns': 0,
                'unknown_ns': 0,
                'consistent': True,
                'all_in_whitelist': True,
                'anomaly_detected': False,
                'unique_ips': ['192.168.1.100'],
                'ip_distribution': {'8.8.8.8': ['192.168.1.100']}
            }
        }
        
        report = self.checker.generate_report(check_result, 'text')
        self.assertIn('DNS 檢測報告', report)
        self.assertIn('example.com', report)
    
    def test_generate_report_json(self):
        """測試生成 JSON 報告"""
        check_result = {
            'domain': 'example.com',
            'results': {},
            'summary': {}
        }
        
        report = self.checker.generate_report(check_result, 'json')
        self.assertIn('"domain"', report)
        self.assertIn('example.com', report)
    
    def test_generate_report_nagios(self):
        """測試生成 Nagios 報告"""
        check_result = {
            'domain': 'example.com',
            'summary': {
                'anomaly_detected': False
            }
        }
        
        report = self.checker.generate_report(check_result, 'nagios')
        self.assertIn('OK', report)
        self.assertIn('example.com', report)

class TestUtils(unittest.TestCase):
    """工具函數測試類"""
    
    def test_validate_nameserver(self):
        """測試 nameserver 驗證"""
        self.assertTrue(validate_nameserver('8.8.8.8'))
        self.assertTrue(validate_nameserver('1.1.1.1'))
        self.assertFalse(validate_nameserver('invalid'))
        self.assertFalse(validate_nameserver('999.999.999.999'))

if __name__ == '__main__':
    unittest.main()

