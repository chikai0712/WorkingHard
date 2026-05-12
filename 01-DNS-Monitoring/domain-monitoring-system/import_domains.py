"""批量匯入域名清單"""
import json
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Domain


def import_domains_from_json(json_file: str):
    """
    從 JSON 檔案批量匯入域名
    
    JSON 格式範例:
    [
        {
            "domain": "example.com",
            "expected_ips": ["1.2.3.4"],
            "expected_ns": ["ns1.example.com"],
            "keyword": "Welcome",
            "check_interval": 300
        }
    ]
    """
    db = SessionLocal()
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            domains_data = json.load(f)
        
        success_count = 0
        skip_count = 0
        
        for data in domains_data:
            # 檢查是否已存在
            existing = db.query(Domain).filter(Domain.domain == data['domain']).first()
            if existing:
                print(f"⚠️  跳過已存在的域名: {data['domain']}")
                skip_count += 1
                continue
            
            # 建立新域名
            domain = Domain(
                domain=data['domain'],
                expected_ips=data['expected_ips'],
                expected_ns=data['expected_ns'],
                keyword=data.get('keyword'),
                check_interval=data.get('check_interval', 300)
            )
            
            db.add(domain)
            success_count += 1
            print(f"✅ 新增域名: {data['domain']}")
        
        db.commit()
        
        print(f"\n匯入完成!")
        print(f"  - 成功新增: {success_count} 個")
        print(f"  - 跳過重複: {skip_count} 個")
        
    except Exception as e:
        print(f"❌ 匯入失敗: {e}")
        db.rollback()
    finally:
        db.close()


def import_domains_from_csv(csv_file: str):
    """
    從 CSV 檔案批量匯入域名
    
    CSV 格式:
    domain,expected_ips,expected_ns,keyword,check_interval
    example.com,"1.2.3.4,5.6.7.8","ns1.example.com,ns2.example.com",Welcome,300
    """
    import csv
    
    db = SessionLocal()
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            success_count = 0
            skip_count = 0
            
            for row in reader:
                # 檢查是否已存在
                existing = db.query(Domain).filter(Domain.domain == row['domain']).first()
                if existing:
                    print(f"⚠️  跳過已存在的域名: {row['domain']}")
                    skip_count += 1
                    continue
                
                # 解析 IP 和 NS 列表
                expected_ips = [ip.strip() for ip in row['expected_ips'].split(',')]
                expected_ns = [ns.strip() for ns in row['expected_ns'].split(',')]
                
                # 建立新域名
                domain = Domain(
                    domain=row['domain'],
                    expected_ips=expected_ips,
                    expected_ns=expected_ns,
                    keyword=row.get('keyword', ''),
                    check_interval=int(row.get('check_interval', 300))
                )
                
                db.add(domain)
                success_count += 1
                print(f"✅ 新增域名: {row['domain']}")
            
            db.commit()
            
            print(f"\n匯入完成!")
            print(f"  - 成功新增: {success_count} 個")
            print(f"  - 跳過重複: {skip_count} 個")
            
    except Exception as e:
        print(f"❌ 匯入失敗: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方式:")
        print("  python import_domains.py domains.json")
        print("  python import_domains.py domains.csv")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if file_path.endswith('.json'):
        import_domains_from_json(file_path)
    elif file_path.endswith('.csv'):
        import_domains_from_csv(file_path)
    else:
        print("❌ 不支援的檔案格式,請使用 .json 或 .csv")

