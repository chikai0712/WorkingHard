"""
GlobalpingChecker V4.1 - Domain Checker
使用 Globalping API 檢測域名狀態
即時寫入模式：每檢測一個域名立即寫入資料庫
"""
import asyncio
import httpx
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from .config import get_settings
from .models import (
    Domain, DomainResult, NodeDetail, TestBatch,
    DomainStatus, DomainZone, CycleType
)
from .database import get_db_session, SessionLocal
from .zone_manager import ZoneManager

settings = get_settings()

# ── 全局即時進度狀態（供 /api/progress 查詢）────────────────────
_check_progress: Dict = {
    "running": False,
    "current_domain": None,
    "current_index": 0,
    "total_domains": 0,
    "current_node_isp": None,
    "current_node_top": None,
    "current_node_city": None,
    "last_result": None,  # {domain, status, isp, top, city, error}
    "recent_results": [],  # 最近 20 筆結果 {domain, status, isp, top, city, error, time}
    "started_at": None,
    "cycle_type": None,
    "stats": {"clean": 0, "blocked": 0, "timeout": 0, "warning": 0, "partial": 0, "api_error": 0},
}


class GlobalpingChecker:
    """Globalping API 域名檢測器"""

    # 預設封鎖 IP（fallback，當檔案無法讀取時使用）
    _DEFAULT_BLOCKED_IPS = {"36.86.63.185"}

    def __init__(self):
        self.api_url = settings.globalping_api_url
        self.token = settings.globalping_token
        self.target_countries = settings.target_country_list
        self.target_country_names = settings.target_country_name_list
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        self.BLOCKED_IPS = self._load_blocked_ips()

    def _load_blocked_ips(self) -> set:
        """
        從 blocked_ips.txt 讀取封鎖 IP 清單。
        每行一個 IP，# 開頭或空行略過。
        讀取失敗時使用預設清單。
        """
        try:
            filepath = settings.blocked_ips_file
            ips = set()
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    # 支援行內注釋，如 "1.2.3.4  # 說明"
                    ip = line.split("#")[0].strip()
                    if ip:
                        ips.add(ip)
            if ips:
                print(f"📋 已載入 {len(ips)} 個封鎖 IP（來源: {filepath}）")
                return ips
            else:
                print(f"⚠️  {filepath} 無有效 IP，使用預設清單")
                return self._DEFAULT_BLOCKED_IPS.copy()
        except FileNotFoundError:
            print(f"⚠️  找不到 blocked_ips.txt，使用預設清單")
            return self._DEFAULT_BLOCKED_IPS.copy()
        except Exception as e:
            print(f"⚠️  讀取封鎖 IP 清單失敗: {e}，使用預設清單")
            return self._DEFAULT_BLOCKED_IPS.copy()
    
    async def check_api_limits(self, client: httpx.AsyncClient) -> Dict:
        """檢查 API 額度"""
        try:
            response = await client.get(
                f"{self.api_url}/limits",
                headers=self.headers,
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️  無法獲取 API 額度: HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"⚠️  檢查額度時發生錯誤: {e}")
            return None
    
    def calculate_required_calls(self, domain_count: int) -> int:
        """計算需要的 API 調用次數
        每個域名每個國家需要 2 次調用：1 次創建測量 + 1 次獲取結果
        """
        countries_count = len(self.target_countries)
        return domain_count * countries_count * 2
    
    async def check_single_domain(self, client: httpx.AsyncClient, domain: str) -> Dict:
        """檢測單個域名 - 使用節點池中已驗證的節點"""
        from .node_pool import NodePoolManager
        
        all_nodes = []
        all_errors = []
        
        # 為每個目標國家創建測量請求
        for country in self.target_countries:
            try:
                # 嘗試從節點池獲取已驗證的節點
                node_ids = []
                try:
                    node_pool = NodePoolManager()
                    node_ids = node_pool.get_country_nodes(country, limit=3)
                except Exception as e:
                    print(f"   ⚠️  {country} 節點池查詢失敗: {e}，使用國家過濾")
                
                if not node_ids:
                    print(f"   ⚠️  {country} 節點池為空，使用國家過濾")
                    # 如果節點池為空，回退到國家過濾模式
                    payload = {
                        "type": "http",
                        "target": domain,
                        "limit": 3,
                        "locations": [{"country": country}]
                    }
                else:
                    print(f"   ✅ {country} 使用節點池: {len(node_ids)} 個已驗證節點")
                    # 使用指定的節點 ID
                    payload = {
                        "type": "http",
                        "target": domain,
                        "limit": len(node_ids),
                        "locations": [{"id": node_id} for node_id in node_ids]
                    }
                
                response = await client.post(
                    f"{self.api_url}/measurements",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code != 202:
                    print(f"   ⚠️  {country} API 錯誤: HTTP {response.status_code}")
                    if response.status_code == 429 or response.status_code >= 500:
                        print(f"   ⏸️  檢測到 API 錯誤 ({response.status_code})，等待 60 分鐘後繼續...")
                        await asyncio.sleep(3600)
                    all_errors.append(f"{country}: API returned {response.status_code}")
                    continue
                
                data = response.json()
                measure_id = data.get("id")
                
                if not measure_id:
                    all_errors.append(f"{country}: No measurement ID returned")
                    continue
                
                # 等待結果
                await asyncio.sleep(5)
                
                result_response = await client.get(
                    f"{self.api_url}/measurements/{measure_id}",
                    headers=self.headers,
                    timeout=30.0
                )
                
                if result_response.status_code == 200:
                    result_data = result_response.json()
                    # 解析該國家的結果（使用節點池時不需要驗證）
                    country_nodes = self._parse_country_results_simple(domain, country, result_data)
                    all_nodes.extend(country_nodes)
                    print(f"   ✅ {country} 獲得 {len(country_nodes)} 個節點結果")
                else:
                    all_errors.append(f"{country}: Failed to get results")
                    
            except Exception as e:
                print(f"   ⚠️  {country} 檢測失敗: {e}")
                all_errors.append(f"{country}: {str(e)}")
        
        # 如果所有國家都失敗
        if not all_nodes:
            error_msg = "; ".join(all_errors) if all_errors else "All countries failed"
            print(f"   ❌ {domain} 檢測失敗: {error_msg}")
            return {
                "domain": domain,
                "status": DomainStatus.API_ERROR,
                "error": error_msg,
                "error_analysis": error_msg,
                "nodes": []
            }
        
        # 綜合評估所有國家的節點狀態
        return self._aggregate_results(domain, all_nodes)
    
    def _parse_country_results_simple(self, domain: str, country: str, data: Dict) -> List[Dict]:
        """解析單個國家的結果（簡化版，節點已預先驗證）"""
        nodes = []
        
        for result in data.get("results", []):
            probe = result.get("probe", {})
            result_data = result.get("result", {})
            
            node = {
                "isp": probe.get("network", "Unknown"),
                "asn": str(probe.get("asn", "")),
                "city": probe.get("city", "Unknown"),
                "country": country,
                "node_ip": "",
                "target_ip": result_data.get("resolvedAddress", ""),
                "http_code": result_data.get("statusCode"),
                "response_time_ms": result_data.get("timings", {}).get("total"),
                "error_message": None
            }
            
            resolvers = probe.get("resolvers", [])
            if resolvers:
                node["node_ip"] = resolvers[0] if resolvers[0] != "private" else "private"
            
            target_ip = node["target_ip"]
            http_code = node["http_code"]
            
            if self._is_blocked_ip(target_ip):
                node["status"] = DomainStatus.BLOCKED
            elif not target_ip or http_code == 0 or http_code is None:
                node["status"] = DomainStatus.TIMEOUT
            elif http_code and (200 <= http_code < 400 or http_code == 403):
                node["status"] = DomainStatus.CLEAN
            else:
                node["status"] = DomainStatus.WARNING
            
            nodes.append(node)
        
        return nodes
    
    async def _validate_and_filter_nodes(
        self, 
        domain: str, 
        target_country: str, 
        data: Dict
    ) -> List[Dict]:
        """驗證並過濾節點，只返回目標國家的節點"""
        from .node_validator import NodeValidator
        
        validator = NodeValidator()
        valid_nodes = []
        
        for result in data.get("results", []):
            probe = result.get("probe", {})
            result_data = result.get("result", {})
            
            # 獲取節點信息
            node_country = probe.get("country", "")
            node_ip = ""
            resolvers = probe.get("resolvers", [])
            if resolvers:
                node_ip = resolvers[0] if resolvers[0] != "private" else "private"
            
            # 方法1: 檢查 Globalping 返回的國家
            if node_country != target_country:
                print(f"      ⚠️  過濾節點: {node_country} != {target_country} (來源: Globalping)")
                continue
            
            # 方法2: 如果有公網 IP，使用 IP 地理位置 API 二次驗證
            if node_ip and node_ip != "private":
                ip_validation = await validator.validate_ip(node_ip)
                if ip_validation["country_code"] != target_country:
                    print(f"      ⚠️  過濾節點: IP {node_ip} 屬於 {ip_validation['country_code']} != {target_country} (來源: IP-API)")
                    continue
            
            # 通過驗證，添加節點
            node = {
                "isp": probe.get("network", "Unknown"),
                "asn": str(probe.get("asn", "")),
                "city": probe.get("city", "Unknown"),
                "country": node_country,
                "node_ip": node_ip,
                "target_ip": result_data.get("resolvedAddress", ""),
                "http_code": result_data.get("statusCode"),
                "response_time_ms": result_data.get("timings", {}).get("total"),
                "error_message": None
            }
            
            target_ip = node["target_ip"]
            http_code = node["http_code"]
            
            if self._is_blocked_ip(target_ip):
                node["status"] = DomainStatus.BLOCKED
            elif not target_ip or http_code == 0 or http_code is None:
                node["status"] = DomainStatus.TIMEOUT
            elif http_code and (200 <= http_code < 400 or http_code == 403):
                node["status"] = DomainStatus.CLEAN
            else:
                node["status"] = DomainStatus.WARNING
            
            valid_nodes.append(node)
        
        return valid_nodes
    
    def _aggregate_results(self, domain: str, nodes: List[Dict]) -> Dict:
        """綜合評估所有國家的節點結果"""
        status_counts = {"clean": 0, "blocked": 0, "timeout": 0, "warning": 0}
        
        for node in nodes:
            status = node.get("status")
            if status == DomainStatus.CLEAN:
                status_counts["clean"] += 1
            elif status == DomainStatus.BLOCKED:
                status_counts["blocked"] += 1
            elif status == DomainStatus.TIMEOUT:
                status_counts["timeout"] += 1
            elif status == DomainStatus.WARNING:
                status_counts["warning"] += 1
        
        total_nodes = len(nodes)
        if total_nodes == 0:
            overall_status = DomainStatus.API_ERROR
        elif status_counts["clean"] == total_nodes:
            overall_status = DomainStatus.CLEAN
        elif status_counts["blocked"] == total_nodes:
            overall_status = DomainStatus.BLOCKED
        elif status_counts["timeout"] == total_nodes:
            overall_status = DomainStatus.TIMEOUT
        elif status_counts["warning"] == total_nodes:
            overall_status = DomainStatus.WARNING
        else:
            overall_status = DomainStatus.PARTIAL
        
        error_analysis = self._analyze_error(overall_status, nodes)
        
        return {
            "domain": domain,
            "status": overall_status,
            "nodes": nodes,
            "error": None,
            "error_analysis": error_analysis
        }
    
    def _analyze_error(self, status: DomainStatus, nodes: List[Dict]) -> str:
        """分析錯誤類型並生成說明"""
        if status == DomainStatus.CLEAN:
            return "正常連通"
        elif status == DomainStatus.BLOCKED:
            blocked_ips = set(n["target_ip"] for n in nodes if n.get("status") == DomainStatus.BLOCKED)
            return f"DNS 污染 - 解析到封鎖 IP: {', '.join(blocked_ips)}"
        elif status == DomainStatus.TIMEOUT:
            return "完全超時 - 所有節點無法連接，可能域名失效或 DNS 無法解析"
        elif status == DomainStatus.WARNING:
            http_codes = set(str(n["http_code"]) for n in nodes if n.get("http_code"))
            return f"服務異常 - HTTP 回應碼: {', '.join(http_codes)}"
        elif status == DomainStatus.PARTIAL:
            status_summary = {}
            for n in nodes:
                s = n.get("status", DomainStatus.API_ERROR)
                if isinstance(s, DomainStatus):
                    s = s.value
                status_summary[s] = status_summary.get(s, 0) + 1
            return f"部分異常 - 節點狀態: {status_summary}"
        else:
            return "API 錯誤"
    
    def _is_blocked_ip(self, ip: str) -> bool:
        """檢查是否為已知的污染 IP"""
        if not ip:
            return False
        if ip in self.BLOCKED_IPS:
            return True
        if ip.startswith("10."):
            return True
        return False


def save_single_result(
    db: Session,
    batch_id: int,
    result: Dict,
    zone_manager: ZoneManager
) -> Dict:
    """
    保存單個域名的檢測結果（即時寫入）
    返回: {"zone_changed": bool, "new_zone": str or None}
    """
    domain_name = result["domain"]
    status = result["status"]
    
    # 獲取或創建域名記錄
    domain_record = db.query(Domain).filter(Domain.domain == domain_name).first()
    if not domain_record:
        domain_record = Domain(domain=domain_name, zone=DomainZone.PENDING)
        db.add(domain_record)
        db.flush()
    
    previous_zone = domain_record.zone
    
    # 更新域名狀態（會自動處理區域移動）
    zone_changed, new_zone = zone_manager.update_domain_status(
        domain_name, status, batch_id
    )
    
    # 保存檢測結果
    domain_result = DomainResult(
        batch_id=batch_id,
        domain_id=domain_record.domain_id,
        domain=domain_name,
        overall_status=status,
        previous_zone=previous_zone,
        new_zone=new_zone if zone_changed else previous_zone,
        zone_changed=zone_changed,
        test_date=datetime.utcnow(),
        error_message=result.get("error_analysis", "")
    )
    db.add(domain_result)
    db.flush()
    
    # 保存節點詳情
    for node in result.get("nodes", []):
        node_detail = NodeDetail(
            result_id=domain_result.result_id,
            node_isp=node.get("isp"),
            node_asn=node.get("asn"),
            node_city=node.get("city"),
            node_country=node.get("country", "ID"),
            node_ip=node.get("node_ip"),
            target_ip=node.get("target_ip"),
            status=node.get("status"),
            http_code=node.get("http_code"),
            response_time_ms=node.get("response_time_ms"),
            error_message=node.get("error_message")
        )
        db.add(node_detail)
    
    # 立即提交這個域名的結果
    db.commit()
    
    return {"zone_changed": zone_changed, "new_zone": new_zone}


async def run_cycle_check(
    domains: List[str],
    cycle_id: int,
    cycle_type: CycleType,
    iteration: int
) -> int:
    """
    執行循環檢測 - 即時寫入模式
    每檢測完一個域名就立即寫入資料庫
    包含 API 額度檢查和智能分配
    """
    db = SessionLocal()
    
    try:
        start_time = datetime.utcnow()
        total_domains = len(domains)
        
        # 初始化檢測器
        checker = GlobalpingChecker()
        
        # 檢查 API 額度
        print(f"\n🔍 檢查 API 額度...")
        async with httpx.AsyncClient() as client:
            limits_data = await checker.check_api_limits(client)
            
            if limits_data:
                remaining = limits_data.get('rateLimit', {}).get('measurements', {}).get('create', {}).get('remaining', 0)
                reset_seconds = limits_data.get('rateLimit', {}).get('measurements', {}).get('create', {}).get('reset', 0)
                required_calls = checker.calculate_required_calls(total_domains)
                countries_count = len(checker.target_countries)
                countries_str = ", ".join(checker.target_countries)
                
                print(f"📊 API 額度狀態:")
                print(f"   剩餘額度: {remaining} 次")
                print(f"   需要調用: {required_calls} 次 ({total_domains} 域名 × {countries_count} 國家 × 2)")
                print(f"   檢測國家: {countries_str}")
                print(f"   額度重置: {reset_seconds} 秒後 ({reset_seconds//60} 分鐘)")
                
                if remaining < required_calls:
                    # 計算可以檢測的域名數量
                    max_domains = remaining // (countries_count * 2)
                    print(f"\n⚠️  API 額度不足！")
                    print(f"   本次最多可檢測: {max_domains} 個域名")
                    print(f"   將分批檢測，剩餘 {total_domains - max_domains} 個域名留待下次")
                    
                    # 只檢測額度允許的數量
                    domains = domains[:max_domains]
                    total_domains = len(domains)
                    
                    if total_domains == 0:
                        print(f"❌ 額度不足，跳過本次檢測")
                        print(f"⏰ 等待 {reset_seconds//60} 分鐘後額度重置")
                        return None
                else:
                    print(f"✅ 額度充足，可以完整檢測")
            else:
                print(f"⚠️  無法獲取額度信息，繼續檢測（可能會遇到限制）")
        
        # 先創建批次記錄
        cycle_name = "異常區檢測" if cycle_type == CycleType.ABNORMAL_CHECK else "正常區檢測"
        batch = TestBatch(
            cycle_id=cycle_id,
            cycle_type=cycle_type,
            iteration=iteration,
            test_date=start_time,
            total_domains=total_domains,
            clean_count=0,
            blocked_count=0,
            timeout_count=0,
            warning_count=0,
            partial_count=0,
            api_error_count=0,
            duration_seconds=0,
            notes=f"{cycle_name} - 第 {iteration} 次 (進行中...)"
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        batch_id = batch.batch_id
        
        print(f"📝 批次 #{batch_id} 已建立，開始即時寫入模式")
        
        # 初始化統計和 zone_manager
        stats = {
            "clean": 0, "blocked": 0, "timeout": 0,
            "warning": 0, "partial": 0, "api_error": 0
        }
        moved_to_normal = 0
        moved_to_abnormal = 0
        
        zone_manager = ZoneManager(db)
        
        # 初始化全局進度狀態
        _check_progress["running"] = True
        _check_progress["current_domain"] = None
        _check_progress["current_index"] = 0
        _check_progress["total_domains"] = total_domains
        _check_progress["current_node_isp"] = None
        _check_progress["current_node_top"] = None
        _check_progress["current_node_city"] = None
        _check_progress["last_result"] = None
        _check_progress["recent_results"] = []
        _check_progress["started_at"] = start_time.isoformat()
        _check_progress["cycle_type"] = cycle_type.value
        _check_progress["stats"] = {"clean": 0, "blocked": 0, "timeout": 0, "warning": 0, "partial": 0, "api_error": 0}
        
        # 逐個檢測並即時寫入
        async with httpx.AsyncClient() as client:
            for i, domain in enumerate(domains):
                print(f"🔍 檢測 [{i+1}/{total_domains}]: {domain}")
                
                # 更新進度狀態
                _check_progress["current_domain"] = domain
                _check_progress["current_index"] = i + 1
                _check_progress["current_node_isp"] = None
                _check_progress["current_node_top"] = None
                _check_progress["current_node_city"] = None
                
                # 檢測單個域名
                result = await checker.check_single_domain(client, domain)
                status = result["status"]
                
                # 更新節點進度（取第一個節點的資訊）
                nodes = result.get("nodes", [])
                current_node_isp = "Unknown"
                current_node_top = "其他"
                current_node_city = ""
                
                if nodes:
                    first_node = nodes[0]
                    current_node_isp = first_node.get("isp", "Unknown")
                    current_node_city = first_node.get("city", "")
                    # 嘗試從節點池獲取 ISP 排名
                    try:
                        from .node_pool import NodePoolManager
                        pool_mgr = NodePoolManager()
                        isp_rank = pool_mgr.get_isp_rank(current_node_isp)
                        current_node_top = f"TOP{isp_rank}" if isp_rank <= 30 else "其他"
                    except:
                        current_node_top = "其他"
                    
                    _check_progress["current_node_isp"] = current_node_isp
                    _check_progress["current_node_top"] = current_node_top
                    _check_progress["current_node_city"] = current_node_city
                
                # 獲取錯誤分析信息
                error_analysis = result.get("error_analysis", "")
                
                # 更新 recent_results（最近 20 筆）
                recent_entry = {
                    "domain": domain,
                    "status": status.value if hasattr(status, "value") else str(status),
                    "isp": current_node_isp,
                    "top": current_node_top,
                    "city": current_node_city,
                    "error": error_analysis,
                    "time": datetime.utcnow().isoformat(),
                }
                _check_progress["last_result"] = recent_entry
                recent = _check_progress["recent_results"]
                recent.insert(0, recent_entry)
                _check_progress["recent_results"] = recent[:20]
                
                # 更新統計
                if status == DomainStatus.CLEAN:
                    stats["clean"] += 1
                elif status == DomainStatus.BLOCKED:
                    stats["blocked"] += 1
                elif status == DomainStatus.TIMEOUT:
                    stats["timeout"] += 1
                elif status == DomainStatus.WARNING:
                    stats["warning"] += 1
                elif status == DomainStatus.PARTIAL:
                    stats["partial"] += 1
                else:
                    stats["api_error"] += 1
                
                # 即時保存結果
                save_result = save_single_result(db, batch_id, result, zone_manager)
                
                if save_result["zone_changed"]:
                    if save_result["new_zone"] == DomainZone.NORMAL:
                        moved_to_normal += 1
                    elif save_result["new_zone"] == DomainZone.ABNORMAL:
                        moved_to_abnormal += 1
                
                # 更新批次統計（每 10 個域名更新一次）
                if (i + 1) % 10 == 0 or (i + 1) == total_domains:
                    batch.clean_count = stats["clean"]
                    batch.blocked_count = stats["blocked"]
                    batch.timeout_count = stats["timeout"]
                    batch.warning_count = stats["warning"]
                    batch.partial_count = stats["partial"]
                    batch.api_error_count = stats["api_error"]
                    batch.moved_to_normal = moved_to_normal
                    batch.moved_to_abnormal = moved_to_abnormal
                    batch.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
                    batch.notes = f"{cycle_name} - 第 {iteration} 次 ({i+1}/{total_domains})"
                    db.commit()
                    print(f"   📊 進度: {i+1}/{total_domains} | 正常: {stats['clean']} | 異常: {total_domains - stats['clean'] - stats['api_error']}")
                
                # API 限流控制
                if (i + 1) % 30 == 0 and (i + 1) < total_domains:
                    print(f"⏸️  批次休息 60 秒...")
                    await asyncio.sleep(60)
                else:
                    await asyncio.sleep(8)
        
        # 最終更新批次記錄
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        batch.clean_count = stats["clean"]
        batch.blocked_count = stats["blocked"]
        batch.timeout_count = stats["timeout"]
        batch.warning_count = stats["warning"]
        batch.partial_count = stats["partial"]
        batch.api_error_count = stats["api_error"]
        batch.moved_to_normal = moved_to_normal
        batch.moved_to_abnormal = moved_to_abnormal
        batch.duration_seconds = duration
        batch.notes = f"{cycle_name} - 第 {iteration} 次 (完成)"
        db.commit()
        
        # 輸出結果
        print(f"\n✅ 檢測完成！批次 ID: {batch_id}")
        print(f"   正常: {stats['clean']} | 封鎖: {stats['blocked']} | 超時: {stats['timeout']}")
        print(f"   警告: {stats['warning']} | 部分: {stats['partial']} | 錯誤: {stats['api_error']}")
        print(f"   移至正常區: {moved_to_normal} | 移至異常區: {moved_to_abnormal}")
        print(f"   耗時: {duration:.1f} 秒")
        
        # 檢測完成，重置進度狀態
        _check_progress["running"] = False
        _check_progress["current_domain"] = None
        _check_progress["stats"] = stats.copy()
        
        return batch_id
        
    except Exception as e:
        print(f"❌ 檢測錯誤: {e}")
        _check_progress["running"] = False
        db.rollback()
        raise
    finally:
        db.close()
