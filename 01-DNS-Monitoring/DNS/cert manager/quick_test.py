#!/usr/bin/env python3
"""快速測試腳本 - 不依賴外部套件

用於快速驗證配置檔案格式和基本功能
"""

import json
import os
import sys
from pathlib import Path


def test_config_format(config_path):
    """測試配置檔案格式"""
    print("=" * 60)
    print("測試配置檔案格式")
    print("=" * 60)
    
    if not os.path.exists(config_path):
        print(f"✗ 配置檔案不存在: {config_path}")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("✓ JSON 格式正確")
        
        # 檢查必要欄位
        required_fields = ['alert_threshold_days', 'renew_threshold_days', 'certificates']
        missing = [f for f in required_fields if f not in config]
        
        if missing:
            print(f"✗ 缺少必要欄位: {', '.join(missing)}")
            return False
        
        print(f"✓ 必要欄位完整")
        print(f"  警報閾值: {config['alert_threshold_days']} 天")
        print(f"  更新閾值: {config['renew_threshold_days']} 天")
        print(f"  憑證數量: {len(config['certificates'])}")
        
        # 檢查憑證配置
        for i, cert in enumerate(config['certificates'], 1):
            print(f"\n憑證 {i}:")
            print(f"  域名: {cert.get('domain', 'N/A')}")
            print(f"  憑證路徑: {cert.get('cert_path', 'N/A')}")
            if cert.get('cert_path') and os.path.exists(cert['cert_path']):
                print(f"  ✓ 憑證檔案存在")
            else:
                print(f"  ⚠ 憑證檔案不存在或路徑未設定")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"✗ JSON 格式錯誤: {e}")
        return False
    except Exception as e:
        print(f"✗ 讀取配置時發生錯誤: {e}")
        return False


def test_serverlist_format(serverlist_path):
    """測試伺服器列表格式"""
    print("\n" + "=" * 60)
    print("測試伺服器列表格式")
    print("=" * 60)
    
    if not os.path.exists(serverlist_path):
        print(f"✗ 伺服器列表檔案不存在: {serverlist_path}")
        return False
    
    try:
        with open(serverlist_path, 'r', encoding='utf-8') as f:
            serverlist = json.load(f)
        
        print("✓ JSON 格式正確")
        
        if 'servers' not in serverlist:
            print("✗ 缺少 'servers' 欄位")
            return False
        
        servers = serverlist['servers']
        print(f"✓ 伺服器數量: {len(servers)}")
        
        for i, server in enumerate(servers, 1):
            name = server.get('name', f'Server {i}')
            host = server.get('host', 'N/A')
            enabled = server.get('enabled', True)
            status = "啟用" if enabled else "停用"
            
            print(f"\n伺服器 {i}: {name}")
            print(f"  主機: {host}")
            print(f"  狀態: {status}")
            
            # 檢查必要欄位
            required = ['host', 'username', 'remote_path']
            missing = [f for f in required if f not in server]
            if missing:
                print(f"  ⚠ 缺少欄位: {', '.join(missing)}")
            else:
                print(f"  ✓ 必要欄位完整")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"✗ JSON 格式錯誤: {e}")
        return False
    except Exception as e:
        print(f"✗ 讀取伺服器列表時發生錯誤: {e}")
        return False


def test_certificate_file(cert_path):
    """測試憑證檔案（基本檢查）"""
    print("\n" + "=" * 60)
    print("測試憑證檔案")
    print("=" * 60)
    
    if not cert_path:
        print("⚠ 未提供憑證路徑，跳過此測試")
        return None
    
    if not os.path.exists(cert_path):
        print(f"✗ 憑證檔案不存在: {cert_path}")
        return False
    
    print(f"✓ 憑證檔案存在: {cert_path}")
    
    # 檢查檔案大小
    size = os.path.getsize(cert_path)
    print(f"  檔案大小: {size} bytes")
    
    # 檢查檔案權限
    if os.access(cert_path, os.R_OK):
        print("  ✓ 可讀取")
    else:
        print("  ✗ 無法讀取（權限不足）")
        return False
    
    # 檢查是否為 PEM 格式（簡單檢查）
    try:
        with open(cert_path, 'r') as f:
            content = f.read(100)
            if 'BEGIN CERTIFICATE' in content:
                print("  ✓ 看起來是 PEM 格式")
                return True
            else:
                print("  ⚠ 可能不是 PEM 格式（或檔案開頭不同）")
                return True  # 仍可能是有效的 DER 格式
    except Exception as e:
        print(f"  ⚠ 讀取檔案時發生錯誤: {e}")
        return False


def main():
    """主函數"""
    print("\n" + "=" * 60)
    print("  SSL 憑證管理器 - 快速測試")
    print("=" * 60)
    
    config_path = "config.json"
    serverlist_path = None
    cert_path = None
    
    # 解析參數
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    if len(sys.argv) > 2:
        cert_path = sys.argv[2]
    
    results = []
    
    # 測試配置檔案
    results.append(("配置檔案", test_config_format(config_path)))
    
    # 如果配置檔案存在，檢查 serverlist_path
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            uploader_config = config.get('uploader', {})
            serverlist_path = uploader_config.get('serverlist_path')
            
            if serverlist_path:
                # 展開路徑
                if serverlist_path.startswith('~'):
                    serverlist_path = os.path.expanduser(serverlist_path)
                elif not os.path.isabs(serverlist_path):
                    config_dir = os.path.dirname(os.path.abspath(config_path))
                    serverlist_path = os.path.join(config_dir, serverlist_path)
                
                results.append(("伺服器列表", test_serverlist_format(serverlist_path)))
        except:
            pass
    
    # 測試憑證檔案
    if cert_path:
        result = test_certificate_file(cert_path)
        if result is not None:
            results.append(("憑證檔案", result))
    
    # 總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通過" if result else "✗ 失敗"
        print(f"{status} {name}")
    
    print(f"\n總計: {passed}/{total} 項測試通過")
    
    if passed == total:
        print("\n✓ 基本配置檢查通過！")
        print("\n提示: 要進行完整功能測試，請執行:")
        print("  python verify_cert.py config.json")
        return 0
    else:
        print(f"\n⚠ 有 {total - passed} 項測試失敗，請檢查配置。")
        return 1


if __name__ == '__main__':
    sys.exit(main())

