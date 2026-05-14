#!/usr/bin/env python3
"""
本機驗證腳本 - 節點池功能測試

測試項目：
1. GET /v1/probes 取得印尼節點
2. IP 二次驗證（ip-api.com）
3. TOP10 ISP 優先排序
4. 節點摘要輸出

執行方式：
    source venv/bin/activate
    python test_node_pool.py
"""
import asyncio
import os
import sys

# 讓 Python 找到 app 模組
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 載入 .env
from dotenv import load_dotenv
load_dotenv()


async def test_fetch_probes():
    """測試 1：直接呼叫 /v1/probes，確認 API 可用並有印尼節點"""
    print("\n" + "="*60)
    print("測試 1：呼叫 GET /v1/probes")
    print("="*60)

    import httpx
    token = os.getenv("GLOBALPING_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.globalping.io/v1/probes",
            headers=headers,
            timeout=15.0,
        )
        print(f"HTTP 狀態碼: {resp.status_code}")

        if resp.status_code != 200:
            print(f"❌ 失敗: {resp.text[:300]}")
            return False

        data = resp.json()
        probes = data if isinstance(data, list) else data.get("probes", [])
        print(f"✅ 共取得 {len(probes)} 個在線節點")

        # 統計各國家節點數
        country_counts = {}
        for p in probes:
            cc = p.get("location", {}).get("country", "?")
            country_counts[cc] = country_counts.get(cc, 0) + 1

        print("\n各國家節點數（前 15 名）：")
        for cc, cnt in sorted(country_counts.items(), key=lambda x: -x[1])[:15]:
            marker = " ← 目標" if cc == "ID" else ""
            print(f"  {cc}: {cnt} 個節點{marker}")

        id_count = country_counts.get("ID", 0)
        print(f"\n印尼 (ID) 節點數: {id_count}")
        return id_count > 0


async def test_ip_validation():
    """測試 2：驗證 ip-api.com 功能"""
    print("\n" + "="*60)
    print("測試 2：IP 二次驗證 (ip-api.com)")
    print("="*60)

    from app.node_validator import NodeValidator
    validator = NodeValidator()

    # 測試用 IP（已知的印尼和非印尼 IP）
    test_cases = [
        ("114.122.0.1",   "ID", True,  "印尼 Telkom IP"),
        ("8.8.8.8",       "ID", False, "Google DNS（非印尼）"),
        ("1.1.1.1",       "ID", False, "Cloudflare DNS（非印尼）"),
        ("10.0.0.1",      "ID", False, "私有 IP"),
        ("36.86.63.185",  "ID", True,  "已知封鎖 IP（印尼 Telkom）"),
    ]

    all_passed = True
    for ip, country, expect_valid, label in test_cases:
        result = await validator.validate_ip(ip, expected_country=country)
        status = "✅" if result["is_valid"] == expect_valid else "❌"
        if result["is_valid"] != expect_valid:
            all_passed = False
        print(
            f"  {status} {ip:<18} | {label}\n"
            f"       → 國家: {result['country_code']:<4} | "
            f"城市: {result['city']:<15} | "
            f"ISP: {result['isp'][:40]}\n"
            f"       → is_valid={result['is_valid']} (期望 {expect_valid}) | source={result['source']}"
        )
        await asyncio.sleep(0.5)  # 避免 ip-api.com 限流

    return all_passed


async def test_isp_priority():
    """測試 3：TOP10 ISP 優先排序邏輯"""
    print("\n" + "="*60)
    print("測試 3：TOP10 ISP 優先排序")
    print("="*60)

    from app.node_pool import _isp_priority, _rank_to_brand, INDONESIA_TOP30_ISP

    test_isps = [
        ("PT Telekomunikasi Selular",            1),
        ("PT XL Axiata Tbk",                     2),
        ("PT Indosat Tbk",                        3),
        ("PT Telekomunikasi Indonesia",           4),
        ("PT Eka Mas Republik",                   5),
        ("PT WIRELESS INDONESIA WIN",             6),
        ("PT Starlink Services Indonesia",        7),
        ("PT Smartfren Telecom Tbk",              8),
        ("PT. BIZNET NETWORKS",                   9),
        ("PT. Cyberindo Aditama",                10),
        ("PT Mora Telematika Indonesia",         11),
        ("PT Indonesia Comnets Plus",            12),
        ("Linknet-Fastnet ASN",                  13),
        ("PT Remala Abadi",                      14),
        ("PT. Cemerlang Multimedia",             15),
        ("PT Parsaoran Global Datatrans",        16),
        ("PT Integrasi Jaringan Ekosistem",      17),
        ("MNC Play Media",                       18),
        ("JEMBATAN CITRA NUSANTARA",             19),
        ("JARINGANKU SARANA NUSANTARA",          20),
        ("Some Unknown ISP Co.",                 99),
        ("",                                     99),
    ]

    all_passed = True
    print(f"  {'ISP 名稱':<45} {'期望':>4}  {'實際':>4}  結果")
    print("  " + "-"*65)
    for isp, expected_rank in test_isps:
        actual_rank = _isp_priority(isp)
        ok = actual_rank == expected_rank
        if not ok:
            all_passed = False
        marker = "✅" if ok else "❌"
        brand = _rank_to_brand(actual_rank)
        print(f"  {marker} {isp:<45} {expected_rank:>4}  {actual_rank:>4}  ({brand})")

    return all_passed


async def test_full_fetch_and_sort():
    """測試 4：完整節點抓取 + 驗證 + 排序（全部節點）"""
    print("\n" + "="*60)
    print("測試 4：完整節點驗證（ID 印尼，全部節點）")
    print("="*60)

    import httpx
    from app.node_pool import _isp_priority, _is_private_ip, _rank_to_brand, INDONESIA_TOP30_ISP
    from app.node_validator import NodeValidator

    token = os.getenv("GLOBALPING_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    validator = NodeValidator()

    # 取得所有在線節點
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.globalping.io/v1/probes", headers=headers, timeout=15.0)
        if resp.status_code != 200:
            print(f"❌ /v1/probes 失敗: {resp.status_code}")
            return False
        data = resp.json()
        probes = data if isinstance(data, list) else data.get("probes", [])

    id_probes = [p for p in probes if p.get("location", {}).get("country") == "ID"]
    print(f"Globalping 回報 {len(id_probes)} 個印尼節點，開始逐一驗證...\n")

    verified = []
    filtered = []

    for i, probe in enumerate(id_probes):
        loc = probe.get("location", {})
        resolvers = probe.get("resolvers", [])
        node_ip = resolvers[0] if resolvers and resolvers[0] != "private" else "private"
        probe_id = probe.get("id") or f"ID-{loc.get('city','?')}-{i}"
        isp = loc.get("network", "") or loc.get("isp", "Unknown")
        city = loc.get("city", "Unknown")

        if node_ip and not _is_private_ip(node_ip):
            validation = await validator.validate_ip(node_ip, expected_country="ID")
            if not validation["is_valid"]:
                filtered.append({"node_ip": node_ip, "isp": isp, "city": city,
                                  "actual_country": validation["country_code"],
                                  "actual_isp": validation["isp"]})
                await asyncio.sleep(0.3)
                continue
            # 用驗證結果補充 ISP
            if not isp or isp == "Unknown":
                isp = validation.get("isp", isp)
        # private IP 直接通過

        node = {
            "node_id": probe_id,
            "node_ip": node_ip,
            "city": city,
            "isp": isp,
            "asn": str(loc.get("asn", "")),
            "isp_rank": _isp_priority(isp),
        }
        verified.append(node)
        await asyncio.sleep(0.3)

    # 排序
    verified.sort(key=lambda n: (n["isp_rank"], n["city"]))

    # ── 輸出被過濾的節點 ──────────────────────────────────────
    if filtered:
        print(f"⚠️  過濾掉 {len(filtered)} 個非印尼節點：")
        for n in filtered:
            print(f"   {n['node_ip']:<18} 實際: {n['actual_country']} | {n['actual_isp'][:40]}")
        print()

    # ── TOP30 ISP 覆蓋報告 ────────────────────────────────────
    print(f"✅ 驗證通過: {len(verified)} 個節點（過濾: {len(filtered)} 個）")
    print()
    print("TOP30 ISP 覆蓋報告：")
    print(f"  {'排名':<5} {'品牌':<30} {'節點數':}") 
    print("  " + "-"*45)
    for entry in INDONESIA_TOP30_ISP:
        count = sum(1 for n in verified if n["isp_rank"] == entry["rank"])
        bar = "█" * count if count > 0 else "（無）"
        print(f"  #{entry['rank']:<4} {entry['brand']:<30} {count:2} 個  {bar}")
    other_count = sum(1 for n in verified if n["isp_rank"] == 99)
    print(f"  {'其他':<5} {'其他 ISP':<30} {other_count:2} 個")

    # ── 完整節點列表 ──────────────────────────────────────────
    print()
    print("完整節點列表（依優先級排序）：")
    print(f"  {'排名':<5} {'ISP':<45} {'城市':<15} IP")
    print("  " + "-"*90)
    for n in verified:
        rank_label = f"#{n['isp_rank']}" if n["isp_rank"] < 99 else "其他"
        print(f"  {rank_label:<5} {n['isp']:<45} {n['city']:<15} {n['node_ip']}")

    # ── 排序驗證 ──────────────────────────────────────────────
    ranks = [n["isp_rank"] for n in verified]
    is_sorted = all(ranks[i] <= ranks[i+1] for i in range(len(ranks)-1))
    print(f"\n排序驗證: {'✅ 正確（由小到大）' if is_sorted else '❌ 排序錯誤'}")

    return is_sorted and len(verified) > 0


async def main():
    print("GlobalpingChecker V4.1 - 節點池功能本機驗證")
    print("=" * 60)

    results = {}

    # 測試 1：/v1/probes API
    try:
        results["test1_probes_api"] = await test_fetch_probes()
    except Exception as e:
        print(f"❌ 測試 1 例外: {e}")
        results["test1_probes_api"] = False

    # 測試 2：IP 驗證
    try:
        results["test2_ip_validation"] = await test_ip_validation()
    except Exception as e:
        print(f"❌ 測試 2 例外: {e}")
        results["test2_ip_validation"] = False

    # 測試 3：ISP 排序邏輯
    try:
        results["test3_isp_priority"] = await test_isp_priority()
    except Exception as e:
        print(f"❌ 測試 3 例外: {e}")
        results["test3_isp_priority"] = False

    # 測試 4：完整流程
    try:
        results["test4_full_fetch"] = await test_full_fetch_and_sort()
    except Exception as e:
        print(f"❌ 測試 4 例外: {e}")
        results["test4_full_fetch"] = False

    # 最終結果
    print("\n" + "="*60)
    print("驗證結果總覽")
    print("="*60)
    labels = {
        "test1_probes_api":    "測試 1: /v1/probes API 連線",
        "test2_ip_validation": "測試 2: IP 二次驗證",
        "test3_isp_priority":  "測試 3: TOP30 ISP 排序邏輯",
        "test4_full_fetch":    "測試 4: 完整節點抓取流程",
    }
    all_ok = True
    for key, label in labels.items():
        ok = results.get(key, False)
        if not ok:
            all_ok = False
        print(f"  {'✅' if ok else '❌'}  {label}")

    print()
    if all_ok:
        print("🎉 所有測試通過！節點池功能驗證完成。")
    else:
        print("⚠️  部分測試未通過，請檢查上方輸出。")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
