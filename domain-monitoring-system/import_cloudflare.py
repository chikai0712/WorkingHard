"""從 Cloudflare DNS 備份清單匯入域名"""
import csv
import re
import os

# 設定正確的資料庫連接
os.environ['DATABASE_URL'] = 'postgresql://dms_user:dms_password@postgres:5432/domain_monitoring'

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Domain


def extract_domain_from_account(account_str: str) -> str:
    """
    從帳戶字串提取域名
    例如: "3rd@remotes 78wwin.com" -> "78wwin.com"
    """
    parts = account_str.split()
    if len(parts) >= 2:
        return parts[-1].strip()
    return account_str.strip()


def import_from_cloudflare_backup(csv_file: str):
    """
    從 Cloudflare DNS 備份 CSV 匯入域名
    
    CSV 格式:
    帳戶,域名,狀態,計劃,總請求數,總流量(MB),緩存流量(MB),緩存請求數,DNS查詢數,DNS查詢時間,失敗原因
    3rd@remotes,78wwin.com,active,Free Website,36662,369.14,168.41,29524,6410,7天,
    """
    db = SessionLocal()
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            # 讀取 CSV
            reader = csv.DictReader(f)
            
            success_count = 0
            skip_count = 0
            error_count = 0
            
            for row in reader:
                try:
                    # 提取域名
                    if '域名' in row:
                        domain_name = row['域名'].strip()
                    elif 'B' in row:  # 如果欄位名稱是 B (Excel 匯出可能用欄位名)
                        domain_name = row['B'].strip()
                    else:
                        # 嘗試從帳戶欄位提取
                        account = row.get('帳戶', row.get('A', ''))
                        domain_name = extract_domain_from_account(account)
                    
                    # 驗證域名格式
                    if not domain_name or '.' not in domain_name:
                        print(f"⚠️  跳過無效域名: {domain_name}")
                        skip_count += 1
                        continue
                    
                    # 檢查狀態
                    status = row.get('狀態', row.get('C', 'active')).strip().lower()
                    is_active = (status == 'active')
                    
                    # 檢查是否已存在
                    existing = db.query(Domain).filter(Domain.domain == domain_name).first()
                    if existing:
                        print(f"⚠️  域名已存在: {domain_name}")
                        skip_count += 1
                        continue
                    
                    # 建立新域名 (使用預設值,稍後可以更新)
                    domain = Domain(
                        domain=domain_name,
                        expected_ips=["0.0.0.0"],  # 需要稍後更新
                        expected_ns=["ns1.cloudflare.com", "ns2.cloudflare.com"],  # Cloudflare 預設
                        keyword=None,  # 可選
                        check_interval=300,
                        is_active=is_active
                    )
                    
                    db.add(domain)
                    success_count += 1
                    
                    status_icon = "✅" if is_active else "⏸️"
                    print(f"{status_icon} 新增域名: {domain_name} (狀態: {status})")
                    
                except Exception as e:
                    print(f"❌ 處理失敗: {row.get('域名', 'unknown')} - {e}")
                    error_count += 1
                    continue
            
            db.commit()
            
            print(f"\n{'='*50}")
            print(f"匯入完成!")
            print(f"  ✅ 成功新增: {success_count} 個")
            print(f"  ⚠️  跳過重複: {skip_count} 個")
            print(f"  ❌ 錯誤: {error_count} 個")
            print(f"{'='*50}")
            
            if success_count > 0:
                print(f"\n⚠️  重要提醒:")
                print(f"  1. 所有域名的 expected_ips 預設為 '0.0.0.0'")
                print(f"  2. 請使用 API 更新每個域名的正確 IP 白名單")
                print(f"  3. 可以使用以下命令查看已匯入的域名:")
                print(f"     curl http://localhost:8000/api/domains")
            
    except Exception as e:
        print(f"❌ 匯入失敗: {e}")
        db.rollback()
    finally:
        db.close()


def import_from_google_sheets_export(csv_file: str):
    """
    從 Google Sheets 匯出的 CSV 匯入
    處理可能沒有標題列的情況
    """
    db = SessionLocal()
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            success_count = 0
            skip_count = 0
            
            # 跳過標題列
            start_line = 1 if '帳戶' in lines[0] or '域名' in lines[0] else 0
            
            for line in lines[start_line:]:
                try:
                    parts = line.strip().split(',')
                    if len(parts) < 2:
                        continue
                    
                    # 第二欄是域名
                    domain_name = parts[1].strip()
                    
                    # 驗證域名
                    if not domain_name or '.' not in domain_name or domain_name == '域名':
                        continue
                    
                    # 第三欄是狀態
                    status = parts[2].strip().lower() if len(parts) > 2 else 'active'
                    is_active = (status == 'active')
                    
                    # 檢查是否已存在
                    existing = db.query(Domain).filter(Domain.domain == domain_name).first()
                    if existing:
                        skip_count += 1
                        continue
                    
                    # 建立新域名
                    domain = Domain(
                        domain=domain_name,
                        expected_ips=["0.0.0.0"],
                        expected_ns=["ns1.cloudflare.com", "ns2.cloudflare.com"],
                        keyword=None,
                        check_interval=300,
                        is_active=is_active
                    )
                    
                    db.add(domain)
                    success_count += 1
                    print(f"✅ 新增: {domain_name}")
                    
                except Exception as e:
                    continue
            
            db.commit()
            print(f"\n匯入完成: 成功 {success_count} 個, 跳過 {skip_count} 個")
            
    except Exception as e:
        print(f"❌ 匯入失敗: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方式:")
        print("  python import_cloudflare.py cloudflare_backup.csv")
        print("")
        print("支援的格式:")
        print("  - Cloudflare DNS 備份 CSV")
        print("  - Google Sheets 匯出的 CSV")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    print(f"開始匯入: {csv_file}")
    print("="*50)
    
    # 嘗試標準格式匯入
    import_from_cloudflare_backup(csv_file)

