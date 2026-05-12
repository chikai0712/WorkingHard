"""測試憑證管理器

用於測試憑證管理器的基本功能
"""

import json
import os
import sys
from pathlib import Path

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cert_manager import CertificateManager, CertificateInfo, AlertManager, CertificateRenewer


def test_certificate_info():
    """測試 CertificateInfo 類別"""
    print("測試 CertificateInfo...")
    
    # 建立一個測試憑證資訊（使用不存在的路徑）
    cert_info = CertificateInfo(
        domain="test.example.com",
        cert_path="/tmp/nonexistent.pem",
        auto_renew=True
    )
    
    print(f"域名: {cert_info.domain}")
    print(f"憑證路徑: {cert_info.cert_path}")
    print(f"到期日期: {cert_info.expiry_date}")
    print(f"剩餘天數: {cert_info.days_remaining}")
    print(f"需要更新: {cert_info.needs_renewal(30)}")
    print(f"需要警報: {cert_info.needs_alert(14)}")
    print("✓ CertificateInfo 測試完成\n")


def test_config_loading():
    """測試配置檔案載入"""
    print("測試配置檔案載入...")
    
    # 建立測試配置
    test_config = {
        "alert_threshold_days": 14,
        "renew_threshold_days": 30,
        "certificates": [
            {
                "domain": "test.example.com",
                "cert_path": "/tmp/test.pem",
                "auto_renew": True
            }
        ],
        "alert_methods": {
            "log": {
                "enabled": True
            }
        },
        "renewer": {
            "certbot_path": "certbot",
            "email": "test@example.com"
        }
    }
    
    # 寫入臨時配置檔案
    test_config_path = "/tmp/test_config.json"
    with open(test_config_path, 'w', encoding='utf-8') as f:
        json.dump(test_config, f, indent=2, ensure_ascii=False)
    
    try:
        manager = CertificateManager(test_config_path)
        print(f"配置載入成功")
        print(f"警報閾值: {manager.alert_threshold} 天")
        print(f"更新閾值: {manager.renew_threshold} 天")
        print(f"憑證數量: {len(manager.certificates)}")
        print("✓ 配置檔案載入測試完成\n")
    except Exception as e:
        print(f"✗ 配置檔案載入失敗: {e}\n")
    finally:
        # 清理
        if os.path.exists(test_config_path):
            os.remove(test_config_path)


def test_alert_manager():
    """測試警報管理器"""
    print("測試 AlertManager...")
    
    config = {
        "alert_methods": {
            "log": {
                "enabled": True
            },
            "email": {
                "enabled": False
            },
            "webhook": {
                "enabled": False
            }
        }
    }
    
    alert_manager = AlertManager(config)
    cert_info = CertificateInfo(
        domain="test.example.com",
        cert_path="/tmp/test.pem",
        days_remaining=10
    )
    
    # 測試發送警報（僅日誌模式）
    result = alert_manager.send_alert(cert_info, "測試警報訊息")
    print(f"警報發送結果: {result}")
    print("✓ AlertManager 測試完成\n")


def main():
    """主測試函數"""
    print("=" * 50)
    print("憑證管理器測試")
    print("=" * 50)
    print()
    
    test_certificate_info()
    test_config_loading()
    test_alert_manager()
    
    print("=" * 50)
    print("所有測試完成")
    print("=" * 50)


if __name__ == '__main__':
    main()

