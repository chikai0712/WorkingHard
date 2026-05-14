"""簡單的測試腳本，驗證 dns_manager 模組是否能正常匯入"""

try:
    from dns_manager import DnsManager, RecordSet, ChangePlan
    print("✓ 成功匯入 DnsManager")
    print("✓ 成功匯入 RecordSet")
    print("✓ 成功匯入 ChangePlan")
    
    # 測試 RecordSet
    record = RecordSet(
        name="example.com.",
        type="A",
        ttl=300,
        rrdatas=["1.2.3.4"]
    )
    print(f"\n✓ RecordSet 建立成功: {record.name} {record.type}")
    
    # 測試 ChangePlan
    plan = ChangePlan()
    plan.additions.append(record)
    print(f"✓ ChangePlan 建立成功，包含 {len(plan.additions)} 個新增記錄")
    
    print("\n✅ 所有基本功能測試通過！")
    print("\n注意：要實際使用 DnsManager，你需要：")
    print("1. Google Cloud 專案 ID")
    print("2. 服務帳號金鑰檔案（JSON 格式）")
    print("3. 修改 example.py 中的設定參數")
    
except ImportError as e:
    print(f"❌ 匯入失敗: {e}")
except Exception as e:
    print(f"❌ 測試失敗: {e}")

