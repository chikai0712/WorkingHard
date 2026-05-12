"""使用範例：如何執行 dns_manager.py

此腳本示範如何使用 DnsManager 來管理 Google Cloud DNS。
"""

from dns_manager import DnsManager, RecordSet

# 設定參數
PROJECT_ID = "your-project-id"  # 替換為你的 GCP 專案 ID
SERVICE_ACCOUNT_KEY = "path/to/service-account-key.json"  # 替換為你的服務帳號金鑰檔案路徑
ZONE_NAME = "example-zone"  # 替換為你的 Managed Zone 名稱

def main():
    # 初始化 DnsManager
    manager = DnsManager.from_service_account_file(
        project_id=PROJECT_ID,
        key_path=SERVICE_ACCOUNT_KEY
    )
    
    # 範例 1: 確保 Managed Zone 存在
    print("檢查/建立 Managed Zone...")
    zone_body = {
        "name": ZONE_NAME,
        "dnsName": "example.com.",  # 替換為你的網域名稱
        "description": "Example DNS zone"
    }
    zone = manager.ensure_managed_zone(zone_body)
    print(f"Zone 已就緒: {zone['name']}")
    
    # 範例 2: 列出現有的 DNS 記錄
    print("\n列出現有 DNS 記錄...")
    existing_rrsets = manager.list_rrsets(ZONE_NAME)
    print(f"找到 {len(existing_rrsets)} 筆記錄")
    for rrset in existing_rrsets[:5]:  # 只顯示前 5 筆
        print(f"  - {rrset['name']} {rrset['type']} {rrset.get('rrdatas', [])}")
    
    # 範例 3: 規劃並套用變更
    print("\n規劃 DNS 記錄變更...")
    desired_records = [
        RecordSet(
            name="example.com.",
            type="A",
            ttl=300,
            rrdatas=["1.2.3.4"]
        ),
        RecordSet(
            name="www.example.com.",
            type="CNAME",
            ttl=300,
            rrdatas=["example.com."]
        )
    ]
    
    plan = manager.plan_changes(desired_records, existing_rrsets)
    print(f"計劃新增 {len(plan.additions)} 筆記錄")
    print(f"計劃刪除 {len(plan.deletions)} 筆記錄")
    
    if not plan.is_noop():
        print("\n套用變更...")
        result = manager.apply_changes(ZONE_NAME, plan)
        print(f"變更完成: {result['status']}")
    else:
        print("\n無需變更")

if __name__ == "__main__":
    main()

