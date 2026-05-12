"""使用範例

示範如何使用憑證管理器
"""

import json
import os
from cert_manager import CertificateManager, CertificateInfo


def example_basic_usage():
    """基本使用範例"""
    print("=" * 50)
    print("基本使用範例")
    print("=" * 50)
    
    # 建立配置
    config = {
        "alert_threshold_days": 14,
        "renew_threshold_days": 30,
        "certificates": [
            {
                "domain": "example.com",
                "cert_path": "/etc/letsencrypt/live/example.com/fullchain.pem",
                "key_path": "/etc/letsencrypt/live/example.com/privkey.pem",
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
            "email": "admin@example.com",
            "use_staging": False
        }
    }
    
    # 儲存配置
    config_path = "example_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    try:
        # 建立管理器
        manager = CertificateManager(config_path)
        
        # 檢查所有憑證
        manager.check_all_certificates()
        
        print("\n✓ 檢查完成")
    except Exception as e:
        print(f"\n✗ 錯誤: {e}")
    finally:
        # 清理
        if os.path.exists(config_path):
            os.remove(config_path)


def example_programmatic_usage():
    """程式化使用範例"""
    print("\n" + "=" * 50)
    print("程式化使用範例")
    print("=" * 50)
    
    # 直接建立憑證資訊
    cert_info = CertificateInfo(
        domain="example.com",
        cert_path="/etc/letsencrypt/live/example.com/fullchain.pem",
        auto_renew=True
    )
    
    print(f"域名: {cert_info.domain}")
    print(f"剩餘天數: {cert_info.days_remaining}")
    print(f"需要更新: {cert_info.needs_renewal(30)}")
    print(f"需要警報: {cert_info.needs_alert(14)}")


def example_custom_alert():
    """自訂警報範例"""
    print("\n" + "=" * 50)
    print("自訂警報範例")
    print("=" * 50)
    
    # 配置包含 Email 和 Webhook
    config = {
        "alert_methods": {
            "log": {
                "enabled": True
            },
            "email": {
                "enabled": True,
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "use_tls": True,
                "username": "your-email@gmail.com",
                "password": "your-app-password",
                "from": "your-email@gmail.com",
                "to": ["admin@example.com"]
            },
            "webhook": {
                "enabled": True,
                "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
                "headers": {
                    "Content-Type": "application/json"
                }
            }
        }
    }
    
    from cert_manager import AlertManager
    
    alert_manager = AlertManager(config)
    cert_info = CertificateInfo(
        domain="example.com",
        cert_path="/tmp/test.pem",
        days_remaining=10
    )
    
    # 發送警報
    alert_manager.send_alert(
        cert_info,
        "憑證即將到期，請注意！"
    )
    
    print("✓ 警報已發送")


if __name__ == '__main__':
    print("\n")
    example_basic_usage()
    example_programmatic_usage()
    example_custom_alert()
    print("\n" + "=" * 50)
    print("範例執行完成")
    print("=" * 50)

