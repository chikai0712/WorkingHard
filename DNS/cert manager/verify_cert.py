#!/usr/bin/env python3
"""憑證功能驗證腳本

用於驗證憑證管理器的各項功能，包括：
1. 憑證讀取與解析
2. 到期時間計算
3. 配置檔案載入
4. 伺服器列表讀取
5. 憑證上傳功能（可選）
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cert_manager import (
    CertificateManager,
    CertificateInfo,
    CertificateRenewer,
    CertificateUploader,
    AlertManager
)


def print_section(title):
    """打印章節標題"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(success, message):
    """打印測試結果"""
    status = "✓" if success else "✗"
    color = "\033[92m" if success else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} {message}")


def test_certificate_reading(cert_path):
    """測試憑證讀取功能"""
    print_section("測試 1: 憑證讀取與解析")
    
    if not os.path.exists(cert_path):
        print_result(False, f"憑證檔案不存在: {cert_path}")
        print("提示: 請提供一個有效的憑證檔案路徑")
        return False
    
    try:
        cert_info = CertificateInfo(
            domain="test.example.com",
            cert_path=cert_path,
            auto_renew=True
        )
        
        if cert_info.expiry_date is None:
            print_result(False, "無法讀取憑證到期時間")
            return False
        
        print_result(True, f"憑證檔案讀取成功: {cert_path}")
        print(f"  域名: {cert_info.domain}")
        print(f"  到期日期: {cert_info.expiry_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  剩餘天數: {cert_info.days_remaining} 天")
        print(f"  需要更新 (30天): {cert_info.needs_renewal(30)}")
        print(f"  需要警報 (14天): {cert_info.needs_alert(14)}")
        
        return True
    except Exception as e:
        print_result(False, f"讀取憑證時發生錯誤: {e}")
        return False


def test_config_loading(config_path):
    """測試配置檔案載入"""
    print_section("測試 2: 配置檔案載入")
    
    if not os.path.exists(config_path):
        print_result(False, f"配置檔案不存在: {config_path}")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print_result(True, f"配置檔案讀取成功: {config_path}")
        print(f"  警報閾值: {config.get('alert_threshold_days', 'N/A')} 天")
        print(f"  更新閾值: {config.get('renew_threshold_days', 'N/A')} 天")
        print(f"  憑證數量: {len(config.get('certificates', []))}")
        
        # 測試 CertificateManager 初始化
        try:
            manager = CertificateManager(config_path)
            print_result(True, "CertificateManager 初始化成功")
            print(f"  載入的憑證數量: {len(manager.certificates)}")
            return True
        except Exception as e:
            print_result(False, f"CertificateManager 初始化失敗: {e}")
            return False
            
    except json.JSONDecodeError as e:
        print_result(False, f"JSON 格式錯誤: {e}")
        return False
    except Exception as e:
        print_result(False, f"讀取配置檔案時發生錯誤: {e}")
        return False


def test_serverlist_loading(config_path):
    """測試伺服器列表載入"""
    print_section("測試 3: 伺服器列表載入")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        uploader_config = config.get('uploader', {})
        serverlist_path = uploader_config.get('serverlist_path')
        
        if not serverlist_path:
            print_result(False, "配置中未指定 serverlist_path")
            print("提示: 在 config.json 的 uploader 區塊中添加 serverlist_path")
            return False
        
        # 展開路徑
        if serverlist_path.startswith('~'):
            serverlist_path = os.path.expanduser(serverlist_path)
        elif not os.path.isabs(serverlist_path):
            config_dir = os.path.dirname(os.path.abspath(config_path))
            serverlist_path = os.path.join(config_dir, serverlist_path)
        
        if not os.path.exists(serverlist_path):
            print_result(False, f"伺服器列表檔案不存在: {serverlist_path}")
            return False
        
        try:
            with open(serverlist_path, 'r', encoding='utf-8') as f:
                serverlist = json.load(f)
            
            servers = serverlist.get('servers', [])
            print_result(True, f"伺服器列表讀取成功: {serverlist_path}")
            print(f"  伺服器數量: {len(servers)}")
            
            enabled_count = sum(1 for s in servers if s.get('enabled', True))
            print(f"  啟用的伺服器: {enabled_count}")
            
            for i, server in enumerate(servers, 1):
                name = server.get('name', f'Server {i}')
                host = server.get('host', 'N/A')
                enabled = server.get('enabled', True)
                status = "啟用" if enabled else "停用"
                print(f"    {i}. {name} ({host}) - {status}")
            
            # 測試 CertificateUploader 初始化
            try:
                uploader = CertificateUploader(uploader_config)
                print_result(True, "CertificateUploader 初始化成功")
                return True
            except Exception as e:
                print_result(False, f"CertificateUploader 初始化失敗: {e}")
                return False
                
        except json.JSONDecodeError as e:
            print_result(False, f"伺服器列表 JSON 格式錯誤: {e}")
            return False
            
    except Exception as e:
        print_result(False, f"讀取伺服器列表時發生錯誤: {e}")
        return False


def test_certificate_check(config_path, check_only=True):
    """測試憑證檢查功能"""
    print_section("測試 4: 憑證檢查功能")
    
    try:
        manager = CertificateManager(config_path)
        
        if len(manager.certificates) == 0:
            print_result(False, "配置中沒有憑證")
            return False
        
        print_result(True, f"開始檢查 {len(manager.certificates)} 個憑證")
        print()
        
        all_valid = True
        for cert_info in manager.certificates:
            print(f"憑證: {cert_info.domain}")
            print(f"  路徑: {cert_info.cert_path}")
            
            if cert_info.expiry_date is None:
                print_result(False, f"  無法讀取憑證: {cert_info.domain}")
                all_valid = False
                continue
            
            print_result(True, f"  到期日期: {cert_info.expiry_date.strftime('%Y-%m-%d')}")
            print(f"  剩餘天數: {cert_info.days_remaining} 天")
            
            if cert_info.needs_renewal(manager.renew_threshold):
                print(f"  ⚠️  需要更新 (剩餘 {cert_info.days_remaining} 天 <= {manager.renew_threshold} 天)")
            else:
                print(f"  ✓ 不需要更新")
            
            if cert_info.needs_alert(manager.alert_threshold):
                print(f"  ⚠️  需要警報 (剩餘 {cert_info.days_remaining} 天 <= {manager.alert_threshold} 天)")
            else:
                print(f"  ✓ 不需要警報")
            
            print()
        
        return all_valid
        
    except Exception as e:
        print_result(False, f"檢查憑證時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_renewer_config(config_path):
    """測試更新器配置"""
    print_section("測試 5: 憑證更新器配置")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        renewer_config = config.get('renewer', {})
        
        if not renewer_config:
            print_result(False, "配置中沒有 renewer 設定")
            return False
        
        print_result(True, "更新器配置讀取成功")
        print(f"  Certbot 路徑: {renewer_config.get('certbot_path', 'certbot')}")
        print(f"  Email: {renewer_config.get('email', 'N/A')}")
        print(f"  Webroot: {renewer_config.get('webroot', 'N/A')}")
        print(f"  使用測試環境: {renewer_config.get('use_staging', False)}")
        print(f"  保存目錄: {renewer_config.get('save_dir', 'N/A')}")
        
        # 檢查 certbot 是否可用
        certbot_path = renewer_config.get('certbot_path', 'certbot')
        import shutil
        if shutil.which(certbot_path):
            print_result(True, f"Certbot 可執行檔存在: {certbot_path}")
        else:
            print_result(False, f"Certbot 可執行檔不存在: {certbot_path}")
            print("提示: 請安裝 certbot 或檢查路徑設定")
        
        # 測試 CertificateRenewer 初始化
        try:
            renewer = CertificateRenewer(renewer_config)
            print_result(True, "CertificateRenewer 初始化成功")
            return True
        except Exception as e:
            print_result(False, f"CertificateRenewer 初始化失敗: {e}")
            return False
            
    except Exception as e:
        print_result(False, f"讀取更新器配置時發生錯誤: {e}")
        return False


def test_alert_config(config_path):
    """測試警報配置"""
    print_section("測試 6: 警報系統配置")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        alert_methods = config.get('alert_methods', {})
        
        if not alert_methods:
            print_result(False, "配置中沒有 alert_methods 設定")
            return False
        
        print_result(True, "警報配置讀取成功")
        
        # 檢查各種警報方式
        log_enabled = alert_methods.get('log', {}).get('enabled', False)
        email_enabled = alert_methods.get('email', {}).get('enabled', False)
        webhook_enabled = alert_methods.get('webhook', {}).get('enabled', False)
        
        print(f"  日誌警報: {'啟用' if log_enabled else '停用'}")
        print(f"  Email 警報: {'啟用' if email_enabled else '停用'}")
        print(f"  Webhook 警報: {'啟用' if webhook_enabled else '停用'}")
        
        # 測試 AlertManager 初始化
        try:
            alert_manager = AlertManager(config)
            print_result(True, "AlertManager 初始化成功")
            return True
        except Exception as e:
            print_result(False, f"AlertManager 初始化失敗: {e}")
            return False
            
    except Exception as e:
        print_result(False, f"讀取警報配置時發生錯誤: {e}")
        return False


def create_test_certificate(output_path):
    """創建一個測試用的自簽名憑證（用於測試）"""
    print_section("創建測試憑證")
    
    try:
        import subprocess
        
        # 創建臨時目錄
        cert_dir = os.path.dirname(output_path)
        if cert_dir and not os.path.exists(cert_dir):
            os.makedirs(cert_dir)
        
        # 使用 openssl 創建自簽名憑證（有效期 365 天）
        cmd = [
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
            '-keyout', output_path.replace('.pem', '.key'),
            '-out', output_path,
            '-days', '365',
            '-nodes',
            '-subj', '/CN=test.example.com/O=Test/C=TW'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print_result(True, f"測試憑證創建成功: {output_path}")
            print(f"  憑證檔案: {output_path}")
            print(f"  私鑰檔案: {output_path.replace('.pem', '.key')}")
            return True
        else:
            print_result(False, f"創建測試憑證失敗: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print_result(False, "找不到 openssl 命令")
        print("提示: 請安裝 openssl 或使用現有的憑證檔案")
        return False
    except Exception as e:
        print_result(False, f"創建測試憑證時發生錯誤: {e}")
        return False


def main():
    """主函數"""
    print("\n" + "=" * 60)
    print("  SSL 憑證管理器 - 功能驗證腳本")
    print("=" * 60)
    
    # 解析命令行參數
    config_path = "config.json"
    cert_path = None
    create_test_cert = False
    
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    if len(sys.argv) > 2:
        cert_path = sys.argv[2]
    if '--create-test-cert' in sys.argv:
        create_test_cert = True
    
    # 檢查配置檔案
    if not os.path.exists(config_path):
        print(f"\n錯誤: 配置檔案不存在: {config_path}")
        print("提示: 請先創建 config.json 或指定配置檔案路徑")
        print("用法: python verify_cert.py [config.json] [cert.pem] [--create-test-cert]")
        return 1
    
    results = []
    
    # 如果需要創建測試憑證
    if create_test_cert:
        test_cert_path = "/tmp/test_cert.pem"
        if create_test_certificate(test_cert_path):
            cert_path = test_cert_path
    
    # 測試 1: 憑證讀取（如果提供了憑證路徑）
    if cert_path:
        results.append(("憑證讀取", test_certificate_reading(cert_path)))
    else:
        print("\n提示: 跳過憑證讀取測試（未提供憑證路徑）")
        print("用法: python verify_cert.py config.json /path/to/cert.pem")
    
    # 測試 2: 配置檔案載入
    results.append(("配置載入", test_config_loading(config_path)))
    
    # 測試 3: 伺服器列表載入
    results.append(("伺服器列表", test_serverlist_loading(config_path)))
    
    # 測試 4: 憑證檢查
    results.append(("憑證檢查", test_certificate_check(config_path)))
    
    # 測試 5: 更新器配置
    results.append(("更新器配置", test_renewer_config(config_path)))
    
    # 測試 6: 警報配置
    results.append(("警報配置", test_alert_config(config_path)))
    
    # 總結
    print_section("測試總結")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通過" if result else "✗ 失敗"
        color = "\033[92m" if result else "\033[91m"
        reset = "\033[0m"
        print(f"{color}{status}{reset} {name}")
    
    print(f"\n總計: {passed}/{total} 項測試通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！系統配置正確。")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 項測試失敗，請檢查配置。")
        return 1


if __name__ == '__main__':
    sys.exit(main())

