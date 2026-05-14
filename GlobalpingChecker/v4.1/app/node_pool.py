"""
GlobalpingChecker V4.1 - Node Pool Manager
管理和驗證節點池

流程：
1. 呼叫 GET /v1/probes 取得 Globalping 所有在線節點（不消耗 measurement 額度）
2. 依 country 過濾出目標國家（預設 ID 印尼）
3. 用 ip-api.com 二次驗證節點公網 IP 確實在目標國家
4. 依 TOP20 ISP 優先序排列，其餘節點附後
5. 存入 node_pool 資料表供 checker.py 取用
"""
import asyncio
import httpx
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean

from .database import Base, SessionLocal
from .node_validator import NodeValidator
from .config import get_settings

settings = get_settings()


# ==================== TOP30 印尼 ISP 優先清單 ====================
# rank 越小越優先；不在清單的節點 rank = 99（排在最後）
INDONESIA_TOP30_ISP: List[Dict] = [
    # ── 依玩家實際 ISP 佔比排序 ──────────────────────────────────
    {"rank": 1,  "brand": "Telkomsel",                        "top": "TOP1",  "keywords": ["PT Telekomunikasi Selular", "Telkomsel"]},
    {"rank": 2,  "brand": "XL Axiata",                        "top": "TOP2",  "keywords": ["PT XL Axiata", "XL Axiata"]},
    {"rank": 3,  "brand": "Indosat Ooredoo Hutchison",        "top": "TOP3",  "keywords": ["PT Indosat", "Indosat", "Ooredoo", "Hutchison", "INDOSAT"]},
    {"rank": 4,  "brand": "Telkom / IndiHome",                "top": "TOP4",  "keywords": ["PT Telekomunikasi Indonesia", "Telkom", "IndiHome"]},
    {"rank": 5,  "brand": "MyRepublic",                       "top": "TOP5",  "keywords": ["PT Eka Mas Republik", "Eka Mas Republik", "MyRepublic"]},
    {"rank": 6,  "brand": "Wireless Indonesia (WIN)",         "top": "TOP6",  "keywords": ["PT WIRELESS INDONESIA WIN", "WIRELESS INDONESIA WIN", "WIN"]},
    {"rank": 7,  "brand": "Starlink Indonesia",               "top": "TOP7",  "keywords": ["PT Starlink Services Indonesia", "Starlink Services Indonesia", "Starlink"]},
    {"rank": 8,  "brand": "Smartfren",                        "top": "TOP8",  "keywords": ["PT Smartfren Telecom", "Smartfren"]},
    {"rank": 9,  "brand": "Biznet",                           "top": "TOP9",  "keywords": ["PT. BIZNET NETWORKS", "BIZNET NETWORKS", "Biznet"]},
    {"rank": 10, "brand": "CBN",                              "top": "TOP10", "keywords": ["CBN", "PT Cyberindo Aditama", "Cyberindo Aditama"]},
    {"rank": 11, "brand": "Oxygen.id / Moratelindo",          "top": "TOP11", "keywords": ["PT Mora Telematika Indonesia", "Moratelindo", "Oxygen"]},
    {"rank": 12, "brand": "Iconnet / PLN",                    "top": "TOP12", "keywords": ["PT Indonesia Comnets Plus", "Indonesia Comnets Plus", "Iconnet", "PLN"]},
    {"rank": 13, "brand": "Linknet / Fastnet",                "top": "TOP13", "keywords": ["Linknet-Fastnet", "PT Link Net", "First Media", "Link Net", "Fastnet", "Linknet"]},
    {"rank": 14, "brand": "PT Remala Abadi",                  "top": "TOP14", "keywords": ["PT Remala Abadi", "Remala Abadi"]},
    {"rank": 15, "brand": "PT Cemerlang Multimedia",          "top": "TOP15", "keywords": ["PT Cemerlang Multimedia", "Cemerlang Multimedia"]},
    {"rank": 16, "brand": "PT Parsaoran Global Datatrans",    "top": "TOP16", "keywords": ["PT Parsaoran Global Datatrans", "Parsaoran"]},
    {"rank": 17, "brand": "PT Integrasi Jaringan Ekosistem",  "top": "TOP17", "keywords": ["PT Integrasi Jaringan Ekosistem", "Integrasi Jaringan"]},
    {"rank": 18, "brand": "MNC Play",                         "top": "TOP18", "keywords": ["MNC Play", "PT MNC Kabel Mediacom"]},
    {"rank": 19, "brand": "Jembatan Citra Nusantara",         "top": "TOP19", "keywords": ["JEMBATAN CITRA NUSANTARA", "Jembatan Citra"]},
    {"rank": 20, "brand": "Jaringanku Sarana Nusantara",      "top": "TOP20", "keywords": ["JARINGANKU SARANA NUSANTARA", "Jaringanku"]},
    # ── 延伸清單（rank 21+，仍優先於 rank 99 其他）────────────────
    {"rank": 21, "brand": "Fiberstar",                        "top": "TOP21", "keywords": ["Fiberstar", "PT Fiberstar"]},
    {"rank": 22, "brand": "Media Sarana Data",                "top": "TOP22", "keywords": ["Media Sarana Data"]},
    {"rank": 23, "brand": "Citraweb",                         "top": "TOP23", "keywords": ["CITRAWEB", "Citraweb"]},
    {"rank": 24, "brand": "Lintas Data Prima",                "top": "TOP24", "keywords": ["Lintas Data Prima"]},
    {"rank": 25, "brand": "PT Lintas Jaringan Nusantara",     "top": "TOP25", "keywords": ["PT Lintas Jaringan Nusantara", "Lintas Jaringan Nusantara"]},
    {"rank": 26, "brand": "Satu Visi Indonesia",              "top": "TOP26", "keywords": ["Satu Visi", "PT Satu Visi", "PT Satu Visi Indonesia"]},
    {"rank": 27, "brand": "JASNITA TELEKOMINDO",              "top": "TOP27", "keywords": ["Jasnita", "PT Jasnita Telekomindo"]},
    {"rank": 28, "brand": "PT Jala Lintas Media",             "top": "TOP28", "keywords": ["PT Jala Lintas Media", "Jala Lintas"]},
    {"rank": 29, "brand": "Pandawa Lima",                     "top": "TOP29", "keywords": ["Pandawa Lima", "PT Pandawa Lima"]},
    {"rank": 30, "brand": "Solnet Indonesia",                 "top": "TOP30", "keywords": ["Solnet Indonesia", "Solnet"]},
]

_ISP_RANK_DEFAULT = 99  # 不在 TOP30 的預設排名


def _isp_priority(isp_name: str) -> int:
    """回傳 ISP 在 TOP10 清單中的排名（越小越優先）。不在清單內回傳 99。"""
    if not isp_name:
        return _ISP_RANK_DEFAULT
    isp_upper = isp_name.upper()
    for entry in INDONESIA_TOP30_ISP:
        if any(kw.upper() in isp_upper for kw in entry["keywords"]):
            return entry["rank"]
    return _ISP_RANK_DEFAULT


def _rank_to_brand(rank: int) -> str:
    """將排名轉換為品牌名稱"""
    for entry in INDONESIA_TOP30_ISP:
        if entry["rank"] == rank:
            return entry["brand"]
    return "其他 ISP"


def _is_private_ip(ip: str) -> bool:
    """判斷是否為私有 IP"""
    if not ip:
        return True
    return (
        ip.startswith("10.") or
        ip.startswith("192.168.") or
        ip.startswith("172.") or
        ip == "private"
    )


# ==================== 資料模型 ====================

class NodePool(Base):
    """節點池數據表"""
    __tablename__ = "node_pool"

    id            = Column(Integer, primary_key=True, index=True)
    node_id       = Column(String, unique=True, index=True)  # Globalping probe ID
    node_ip       = Column(String)
    country       = Column(String, index=True)               # 國家代碼, e.g. ID
    country_name  = Column(String)
    city          = Column(String)
    isp           = Column(String)
    asn           = Column(String)
    isp_rank      = Column(Integer, default=_ISP_RANK_DEFAULT)  # TOP30 排名
    is_active     = Column(Boolean, default=True)
    last_verified = Column(DateTime)
    created_at    = Column(DateTime, default=datetime.now)


# ==================== 管理器 ====================

class NodePoolManager:
    """節點池管理器"""

    PROBES_URL = "https://api.globalping.io/v1/probes"

    def __init__(self):
        self.api_url          = settings.globalping_api_url
        self.token            = settings.globalping_token
        self.headers          = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.validator        = NodeValidator()
        self.target_countries = settings.target_country_list

    # ------------------------------------------------------------------
    # 公開 API
    # ------------------------------------------------------------------

    async def initialize_node_pool(self):
        """初始化節點池：抓取 → 驗證 → 排序 → 存庫"""
        print("🔍 初始化節點池...")

        for country in self.target_countries:
            print(f"   [{country}] 從 Globalping /v1/probes 抓取節點...")
            nodes = await self.fetch_country_nodes(country)

            if nodes:
                await self.save_nodes_to_db(nodes, country)
                top30_count = sum(1 for n in nodes if n["isp_rank"] <= 30)
                print(
                    f"   ✅ [{country}] 已儲存 {len(nodes)} 個驗證節點 "
                    f"(TOP30 ISP: {top30_count} 個)"
                )
                self._print_node_summary(nodes[:15])
            else:
                print(f"   ⚠️  [{country}] 未找到可用節點")

    async def fetch_country_nodes(self, country: str) -> List[Dict]:
        """
        主要流程：
        1. GET /v1/probes  → 取得所有在線 probe（不消耗額度）
        2. 過濾出 country 符合的 probe
        3. 對每個公網 IP 用 ip-api.com 二次驗證國家
        4. 計算 TOP10 ISP 優先級
        5. 依 isp_rank ASC 排序後回傳
        """
        raw_probes = await self._fetch_all_probes()

        if not raw_probes:
            # /v1/probes 失敗時 fallback 至 measurement 探索
            print(f"   ⚠️  [{country}] /v1/probes 無回應，改用 measurement 探索")
            return await self._fetch_via_measurement(country)

        # ── Step 2: 過濾目標國家 ──────────────────────────────────────
        country_probes = [
            p for p in raw_probes
            if p.get("location", {}).get("country") == country
        ]
        print(f"   [{country}] Globalping 回報 {len(country_probes)} 個節點，開始驗證...")

        if not country_probes:
            return []

        # ── Step 3 & 4: IP 驗證 + ISP 排名 ──────────────────────────
        verified_nodes = []
        for i, probe in enumerate(country_probes):
            node = self._probe_to_node(probe, country, index=i)
            node_ip = node["node_ip"]

            if node_ip and not _is_private_ip(node_ip):
                # 公網 IP：用 ip-api.com 驗證是否真的在目標國家
                validation = await self.validator.validate_ip(node_ip, expected_country=country)
                if not validation["is_valid"]:
                    print(
                        f"      ⚠️  過濾: {node_ip} 實際屬於 "
                        f"{validation['country_code']} ({validation['country']})"
                    )
                    continue
                # 若 Globalping 未提供 ISP，用驗證結果補充
                if not node["isp"] or node["isp"] == "Unknown":
                    node["isp"] = validation.get("isp", node["isp"])
            # private IP：信任 Globalping 的 country 標記，跳過 IP 驗證

            node["isp_rank"] = _isp_priority(node["isp"])
            verified_nodes.append(node)
            await asyncio.sleep(0.3)  # 避免 ip-api.com 被限流

        # ── Step 5: 排序（TOP30 優先，同 rank 內按 city 字母）────────
        verified_nodes.sort(key=lambda n: (n["isp_rank"], n["city"]))

        print(
            f"   [{country}] 驗證通過 {len(verified_nodes)} / {len(country_probes)} 個節點"
        )
        return verified_nodes

    async def save_nodes_to_db(self, nodes: List[Dict], country: str):
        """將節點存入資料庫（先清空該國家節點，再全部重新寫入）"""
        db = SessionLocal()
        saved = 0
        skipped = 0
        try:
            # ── 先清空該國家所有節點，確保資料乾淨 ──────────────────
            db.query(NodePool).filter(NodePool.country == country).delete()
            db.commit()

            # ── 全部重新 INSERT ──────────────────────────────────────
            for node in nodes:
                try:
                    db.add(NodePool(
                        node_id       = node["node_id"],
                        node_ip       = node["node_ip"],
                        country       = node["country"],
                        country_name  = node["country_name"],
                        city          = node["city"],
                        isp           = node["isp"],
                        asn           = node["asn"],
                        isp_rank      = node["isp_rank"],
                        last_verified = datetime.now(),
                    ))
                    db.commit()
                    saved += 1
                except Exception as e:
                    db.rollback()
                    skipped += 1
                    print(f"      ⚠️  節點寫入失敗: {node.get('node_id')} - {e}")
        finally:
            db.close()
        print(f"      ✅ 成功寫入 {saved} 個節點" + (f"，跳過 {skipped} 個" if skipped else ""))

    def get_country_nodes(self, country: str, limit: int = 3) -> List[str]:
        """
        從資料庫取出指定國家的節點 ID，依 isp_rank ASC 排序。
        優先回傳 TOP30 ISP 節點。
        """
        db = SessionLocal()
        try:
            nodes = (
                db.query(NodePool)
                .filter(NodePool.country == country, NodePool.is_active == True)
                .order_by(NodePool.isp_rank, NodePool.city)
                .all()
            )
            return [n.node_id for n in nodes][:limit]
        finally:
            db.close()

    def get_country_nodes_with_info(self, country: str, limit: int = 10) -> List[Dict]:
        """取出節點並附帶 ISP 資訊（供 debug / dashboard 使用）"""
        db = SessionLocal()
        try:
            nodes = (
                db.query(NodePool)
                .filter(NodePool.country == country, NodePool.is_active == True)
                .order_by(NodePool.isp_rank, NodePool.city)
                .limit(limit)
                .all()
            )
            return [
                {
                    "node_id":   n.node_id,
                    "node_ip":   n.node_ip,
                    "city":      n.city,
                    "isp":       n.isp,
                    "asn":       n.asn,
                    "isp_rank":  n.isp_rank,
                    "isp_brand": _rank_to_brand(n.isp_rank),
                }
                for n in nodes
            ]
        finally:
            db.close()

    async def refresh_node_pool(self):
        """刷新節點池（建議每天執行一次）"""
        print("🔄 刷新節點池...")
        await self.initialize_node_pool()
        print("✅ 節點池刷新完成")

    def get_node_pool_stats(self) -> Dict:
        """取得各國家節點統計，含 TOP10 ISP 覆蓋情況"""
        db = SessionLocal()
        try:
            stats = {}
            for country in self.target_countries:
                nodes = (
                    db.query(NodePool)
                    .filter(NodePool.country == country, NodePool.is_active == True)
                    .order_by(NodePool.isp_rank)
                    .all()
                )
                top30 = [n for n in nodes if n.isp_rank <= 30]
                stats[country] = {
                    "total":       len(nodes),
                    "top30_count": len(top30),
                    "top30_isps":  [
                        {
                            "rank":  n.isp_rank,
                            "brand": _rank_to_brand(n.isp_rank),
                            "isp":   n.isp,
                            "city":  n.city,
                        }
                        for n in top30
                    ],
                }
            return stats
        finally:
            db.close()

    # ------------------------------------------------------------------
    # 私有輔助方法
    # ------------------------------------------------------------------

    async def _fetch_all_probes(self) -> List[Dict]:
        """
        呼叫 GET /v1/probes 取得所有在線 probe 列表。
        此端點不消耗 measurement 額度。
        回傳格式範例：
        [
          {
            "version": "0.28.0",
            "location": {"country": "ID", "city": "Jakarta", ...},
            "tags": [...],
            "resolvers": ["1.2.3.4"],
            ...
          },
          ...
        ]
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.PROBES_URL,
                    headers=self.headers,
                    timeout=15.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    # API 可能回傳 list 或 {"probes": [...]}
                    if isinstance(data, list):
                        return data
                    return data.get("probes", [])
                else:
                    print(f"   ⚠️  /v1/probes 回應 HTTP {response.status_code}")
                    return []
        except Exception as e:
            print(f"   ⚠️  /v1/probes 請求失敗: {e}")
            return []

    def _probe_to_node(self, probe: Dict, country: str, index: int = 0) -> Dict:
        """將 Globalping probe 物件轉換為內部節點格式"""
        import hashlib
        location = probe.get("location", {})
        resolvers = probe.get("resolvers", [])

        node_ip = ""
        if resolvers:
            first = resolvers[0]
            node_ip = first if first != "private" else "private"

        # Globalping probe ID：優先用 probe["id"]，若無則用 city+asn+resolvers+index hash 確保唯一
        probe_id = probe.get("id") or (
            f"{country}-{location.get('city', 'unknown')}-{location.get('asn', '')}-"
            + hashlib.md5((",".join(resolvers) + str(index)).encode()).hexdigest()[:8]
        )

        return {
            "node_id":      probe_id,
            "node_ip":      node_ip,
            "country":      country,
            "country_name": location.get("country", country),
            "city":         location.get("city", "Unknown"),
            "isp":          location.get("network", "") or location.get("isp", "Unknown"),
            "asn":          str(location.get("asn", "")),
            "isp_rank":     _ISP_RANK_DEFAULT,  # 稍後由呼叫方填入
        }

    async def _fetch_via_measurement(self, country: str) -> List[Dict]:
        """
        Fallback：透過送出 ping measurement 探索節點。
        只在 /v1/probes 失敗時使用，會消耗少量 API 額度。
        """
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "type": "ping",
                    "target": "1.1.1.1",
                    "limit": 10,
                    "locations": [{"country": country}],
                }
                resp = await client.post(
                    f"{self.api_url}/measurements",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0,
                )
                if resp.status_code != 202:
                    print(f"   ❌ [{country}] measurement fallback 失敗: HTTP {resp.status_code}")
                    return []

                measure_id = resp.json().get("id")
                if not measure_id:
                    return []

                await asyncio.sleep(6)

                result_resp = await client.get(
                    f"{self.api_url}/measurements/{measure_id}",
                    headers=self.headers,
                    timeout=30.0,
                )
                if result_resp.status_code != 200:
                    return []

                nodes = []
                for result in result_resp.json().get("results", []):
                    probe = result.get("probe", {})
                    if probe.get("country") != country:
                        continue

                    # 包裝成與 _probe_to_node 一致的格式
                    fake_probe = {
                        "id":        None,
                        "location": {
                            "country": probe.get("country", country),
                            "city":    probe.get("city", "Unknown"),
                            "network": probe.get("network", "Unknown"),
                            "asn":     probe.get("asn", ""),
                        },
                        "resolvers": probe.get("resolvers", []),
                    }
                    node = self._probe_to_node(fake_probe, country, index=len(nodes))

                    # 驗證公網 IP
                    if node["node_ip"] and not _is_private_ip(node["node_ip"]):
                        validation = await self.validator.validate_ip(
                            node["node_ip"], expected_country=country
                        )
                        if not validation["is_valid"]:
                            continue

                    node["isp_rank"] = _isp_priority(node["isp"])
                    nodes.append(node)
                    await asyncio.sleep(0.3)

                nodes.sort(key=lambda n: (n["isp_rank"], n["city"]))
                return nodes

        except Exception as e:
            print(f"   ❌ [{country}] measurement fallback 例外: {e}")
            return []

    def _print_node_summary(self, nodes: List[Dict]):
        """印出節點摘要（前 N 個）"""
        print("      排名  ISP                                           城市")
        print("      " + "-" * 65)
        for n in nodes:
            rank_label = f"#{n['isp_rank']}" if n["isp_rank"] < _ISP_RANK_DEFAULT else "其他"
            print(f"      {rank_label:>4}  {n['isp']:<45}  {n['city']}")
                    