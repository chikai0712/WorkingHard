#!/usr/bin/env python3
"""
快速分析當前檢測結果
直接從用戶提供的輸出中提取信息
"""

# 從用戶輸出中提取的數據
results = """
bajitop.com: CLEAN (3/3)
asgcash.com: CLEAN (3/3)
asia999mm.com: CLEAN (3/3)
btop88.com: CLEAN (3/3)
cpc686.com: CLEAN (3/3)
bettro88.com: CLEAN (3/3)
aztecash.win: TIMEOUT (3/3)
dubaibet.co: CLEAN (3/3)
data88.bet: CLEAN (3/3)
cric69.com: CLEAN (3/3)
crownff.com: CLEAN (3/3)
crownsss.com: CLEAN (3/3)
dubaibet.club: PARTIAL (1/3 timeout)
crownjem.com: CLEAN (3/3)
d9bet99.com: CLEAN (3/3)
digtal01.com: TIMEOUT (3/3)
d9bet68.com: CLEAN (3/3)
golden688.com: CLEAN (3/3)
gbw777.com: CLEAN (3/3)
gdr99.com: CLEAN (3/3)
goldnova.site: TIMEOUT (3/3)
fk88.com: WARNING (3/3 - HTTP 500)
gdr66.net: CLEAN (3/3)
grd99.com: CLEAN (3/3)
gh1152.com: CLEAN (3/3)
greybet666.com: CLEAN (3/3)
goldstar88.com: CLEAN (3/3)
kdiwyndhjfdksah.xyz: CLEAN (3/3)
hod77.com: PARTIAL (2/3 clean, 1/3 timeout)
jp88.fun: CLEAN (3/3)
koapp2.com: TIMEOUT (3/3)
jp88.asia: CLEAN (3/3)
koapp1.com: CLEAN (3/3)
koapp3.com: TIMEOUT (3/3)
kd2288.com: CLEAN (3/3)
kd88.net: CLEAN (3/3)
jdn77mm.com: CLEAN (3/3)
luckynine9.com: CLEAN (3/3)
lucky7online.asia: CLEAN (3/3)
liquidbet.com: CLEAN (3/3)
koapp9.com: TIMEOUT (3/3)
koapp4.com: TIMEOUT (3/3)
koapp8.com: TIMEOUT (3/3)
lucky24.xyz: CLEAN (3/3)
koapp7.com: TIMEOUT (3/3)
koapp6.com: TIMEOUT (3/3)
koapp5.com: TIMEOUT (3/3)
mm777global.com: CLEAN (3/3)
mm777global.club: PARTIAL (1/3 timeout, 2/3 clean)
"""

# API 錯誤的域名（從 megawinner88.com 開始）
api_error_domains = [
    "megawinner88.com", "mm777global.online", "mmbet388.com", "maxwin68.club",
    "luckynine9.org", "m57ag.space", "mm777-global.com", "mm777games.com",
    "mw68.fun", "mmoslots.com", "mnm777.org", "pp6688.xyz", "mmbet388.xyz",
    "mnm777.site", "mycrowngem.com", "ngn99mm.com", "mmjdn77.com", "mmobet.vip",
    "saffaluck.co.za", "primebet.asia", "sart88.com", "sb777.online",
    "primebet.cash", "primebet977.com", "roman628.com", "sartrupee.com",
    "sb777special.asia", "sart99.com", "sbo777.app", "sbonation.live",
    "setswel.com", "sbo777.cc", "sbcbet.com", "sbclive.biz", "sbcsport.com",
    "sbclive.co", "sbclive88.org", "shwemyinn.com", "silvawin.org",
    "special9.net", "silvawin.com", "silvawin.net", "silvawin.site",
    "silvawin.pro", "smt696official.com", "sonitagg.com", "sonitalatam.com",
    "sonitasia.com", "subuu.bet", "sunabet.com", "special9.online",
    "subuu.net", "sunarupee.com", "suna88.com"
]

def analyze():
    # 統計
    clean = []
    blocked = []
    timeout = []
    warning = []
    partial = []
    
    for line in results.strip().split('\n'):
        if not line.strip():
            continue
        
        parts = line.split(':')
        if len(parts) < 2:
            continue
        
        domain = parts[0].strip()
        status = parts[1].strip()
        
        if 'CLEAN' in status:
            clean.append(domain)
        elif 'TIMEOUT' in status:
            timeout.append(domain)
        elif 'WARNING' in status:
            warning.append(domain)
        elif 'PARTIAL' in status:
            partial.append(domain)
    
    total = len(clean) + len(timeout) + len(warning) + len(partial) + len(api_error_domains)
    
    print("=" * 80)
    print("域名檢測結果分析報告")
    print("=" * 80)
    print()
    
    print("📊 統計摘要")
    print("-" * 80)
    print(f"總域名數：{total}")
    print(f"✅ 正常連通 (CLEAN):     {len(clean):3d} ({len(clean)*100//total:2d}%)")
    print(f"🚨 DNS 污染 (BLOCKED):   {len(blocked):3d} ({len(blocked)*100//total:2d}%)")
    print(f"⚠️  完全超時 (TIMEOUT):   {len(timeout):3d} ({len(timeout)*100//total:2d}%)")
    print(f"⚠️  服務異常 (WARNING):   {len(warning):3d} ({len(warning)*100//total:2d}%)")
    print(f"🔄 部分異常 (PARTIAL):   {len(partial):3d} ({len(partial)*100//total:2d}%)")
    print(f"❌ 檢測失敗 (API_ERROR): {len(api_error_domains):3d} ({len(api_error_domains)*100//total:2d}%)")
    print()
    
    if timeout:
        print("=" * 80)
        print(f"⚠️  完全超時域名 ({len(timeout)} 個)")
        print("=" * 80)
        print("這些域名在所有 3 個節點都無法解析或連接超時")
        print()
        for domain in timeout:
            print(f"  • {domain}")
        print()
    
    if partial:
        print("=" * 80)
        print(f"🔄 部分異常域名 ({len(partial)} 個)")
        print("=" * 80)
        print("這些域名在不同節點有不同的結果（區域性問題）")
        print()
        for line in results.strip().split('\n'):
            if 'PARTIAL' in line:
                parts = line.split(':')
                domain = parts[0].strip()
                detail = parts[1].strip()
                print(f"  • {domain}")
                print(f"    {detail}")
        print()
    
    if warning:
        print("=" * 80)
        print(f"⚠️  服務異常域名 ({len(warning)} 個)")
        print("=" * 80)
        print("這些域名 DNS 正常但服務器返回錯誤狀態碼")
        print()
        for domain in warning:
            print(f"  • {domain} - HTTP 500 (服務器內部錯誤)")
        print()
    
    if api_error_domains:
        print("=" * 80)
        print(f"❌ 檢測失敗域名 ({len(api_error_domains)} 個)")
        print("=" * 80)
        print("這些域名因 API 頻率限制未能完成檢測，需要重新檢測")
        print()
        for domain in api_error_domains:
            print(f"  • {domain}")
        print()
    
    print("=" * 80)
    print("📋 建議動作")
    print("=" * 80)
    print()
    
    if timeout:
        print("⚠️  完全超時域名：")
        print("  - 檢查域名 DNS 配置")
        print("  - 確認服務器是否正常運行")
        print("  - 檢查防火牆設置")
        print("  - 可能是域名已過期或未配置")
        print()
    
    if partial:
        print("🔄 部分異常域名：")
        print("  - 記錄哪些 ISP/地區有問題")
        print("  - 考慮使用多個 CDN 節點")
        print("  - 監控特定地區的可用性")
        print("  - 這些域名在某些地區可能被封鎖")
        print()
    
    if warning:
        print("⚠️  服務異常域名：")
        print("  - 通知技術團隊檢查服務器")
        print("  - 檢查應用程式日誌")
        print("  - 不是封鎖問題，是網站本身的問題")
        print("  - HTTP 500 表示服務器內部錯誤")
        print()
    
    if api_error_domains:
        print("❌ 檢測失敗域名：")
        print("  - 使用改進版腳本重新檢測：")
        print("    ~/id_globalping_multi_v2.sh ~/failed_domains.txt")
        print("  - 或手動檢測這些域名")
        print("  - 建議增加檢測間隔時間")
        print()
    
    print("=" * 80)
    print("💡 關鍵發現")
    print("=" * 80)
    print()
    print(f"1. 大部分域名正常：{len(clean)} 個域名 ({len(clean)*100//total}%) 可以正常訪問")
    print()
    print(f"2. 完全無法訪問：{len(timeout)} 個域名完全超時")
    print("   - koapp 系列域名 (koapp2-9.com) 全部超時")
    print("   - aztecash.win, digtal01.com, goldnova.site 也超時")
    print("   - 這些可能是域名配置問題或已停用")
    print()
    print(f"3. 區域性問題：{len(partial)} 個域名在部分節點異常")
    print("   - dubaibet.club: 1 個節點超時")
    print("   - hod77.com: 1 個節點超時")
    print("   - mm777global.club: 1 個節點超時")
    print("   - 可能是特定 ISP 的問題")
    print()
    print(f"4. 服務器錯誤：{len(warning)} 個域名返回 HTTP 500")
    print("   - fk88.com: 服務器內部錯誤")
    print("   - 需要檢查網站應用程式")
    print()
    print(f"5. API 限制：{len(api_error_domains)} 個域名未能檢測")
    print("   - 從 megawinner88.com 開始觸發頻率限制")
    print("   - 需要使用改進版腳本重新檢測")
    print()
    print("=" * 80)
    
    # 生成失敗域名清單
    with open('failed_domains.txt', 'w') as f:
        for domain in api_error_domains:
            f.write(domain + '\n')
    
    print()
    print("✅ 失敗域名清單已保存到: failed_domains.txt")
    print()
    print("💡 下一步操作：")
    print("   1. 使用改進版腳本重新檢測失敗的域名：")
    print("      chmod +x ~/id_globalping_multi_v2.sh")
    print("      ~/id_globalping_multi_v2.sh failed_domains.txt")
    print()
    print("   2. 檢查完全超時的域名配置")
    print()
    print("   3. 監控部分異常的域名")
    print()
    print("   4. 修復 fk88.com 的服務器錯誤")
    print()

if __name__ == '__main__':
    analyze()
