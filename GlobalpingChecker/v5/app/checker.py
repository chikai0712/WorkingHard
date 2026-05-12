"""
GlobalpingChecker V5 - Domain Checker

變更自 V4.1：
- 記錄每個域名的 check_duration_ms
- 記錄批次消耗的 api_calls_used
- API Error 等待時間改用 settings.api_quota_wait_on_error
- 節點池查詢失敗時改用 nodes_per_country 設定值
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
from .database import SessionLocal
from .zone_manager import ZoneManager

settings = get_settings()

# 暫停旗標：設為 True 時，run_cycle_check 會在當前域名完成後停止
_stop_flag: bool = False

_check_progress: Dict = {
    "running":           False,
    "current_domain":    None,
    "current_index":     0,
    "total_domains":     0,
    "current_node_isp":  None,
    "current_node_top":  None,
    "current_node_city": None,
    "last_result":       None,
    "recent_results":    [],
    "started_at":        None,
    "cycle_type":        None,
    "stats": {"clean": 0, "blocked": 0, "timeout": 0,
              "warning": 0, "partial": 0, "api_error": 0},
}


class GlobalpingChecker:
    _DEFAULT_BLOCKED_IPS = {"36.86.63.185"}

    def __init__(self):
        self.api_url          = settings.globalping_api_url
        self.token            = settings.globalping_token
        self.target_countries = settings.target_country_list
        self.headers = {
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        self.BLOCKED_IPS = self._load_blocked_ips()

    def _load_blocked_ips(self) -> set:
        try:
            ips = set()
            with open(settings.blocked_ips_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    ip = line.split("#")[0].strip()
                    if ip:
                        ips.add(ip)
            return ips if ips else self._DEFAULT_BLOCKED_IPS.copy()
        except Exception:
            return self._DEFAULT_BLOCKED_IPS.copy()

    async def check_api_limits(self, client: httpx.AsyncClient) -> Optional[Dict]:
        try:
            r = await client.get(
                f"{self.api_url}/limits",
                headers=self.headers, timeout=10.0
            )
            return r.json() if r.status_code == 200 else None
        except Exception:
            return None

    def calculate_required_calls(self, domain_count: int) -> int:
        # DNS 模式：每個域名每個國家需要 2 次 API 呼叫（POST 建立 + GET 取結果）
        # 雖然 DNS 不消耗 credits，但 rate limit 仍以 API 呼叫次數計算
        return domain_count * len(self.target_countries) * 2

    def _is_blocked_ip(self, ip: str) -> bool:
        return bool(ip) and (ip in self.BLOCKED_IPS or ip.startswith("10."))

    def _parse_results_dns(self, data: Dict, country: str) -> List[Dict]:
        """解析 DNS 測量結果（不消耗 credits）"""
        nodes = []
        for result in data.get("results", []):
            probe       = result.get("probe", {})
            result_data = result.get("result", {})
            resolvers   = probe.get("resolvers", [])
            node_ip     = resolvers[0] if resolvers and resolvers[0] != "private" else ""

            # DNS 結果：取第一個 A record
            answers   = result_data.get("answers", []) or []
            target_ip = ""
            for ans in answers:
                if ans.get("type") in ("A", "AAAA"):
                    target_ip = ans.get("value", "")
                    break

            # 狀態判斷
            if result_data.get("status") == "NXDOMAIN" or not answers:
                status = DomainStatus.TIMEOUT
            elif self._is_blocked_ip(target_ip):
                status = DomainStatus.BLOCKED
            else:
                status = DomainStatus.CLEAN

            nodes.append({
                "isp":              probe.get("network", "Unknown"),
                "asn":              str(probe.get("asn", "")),
                "city":             probe.get("city", "Unknown"),
                "country":          country,
                "node_ip":          node_ip,
                "target_ip":        target_ip,
                "http_code":        None,   # DNS 模式無 HTTP code
                "response_time_ms": result_data.get("timings", {}).get("total"),
                "status":           status,
                "error_message":    result_data.get("status"),
            })
        return nodes

    def _parse_results(self, data: Dict, country: str) -> List[Dict]:
        """解析 HTTP 測量結果（消耗 credits，保留備用）"""
        nodes = []
        for result in data.get("results", []):
            probe       = result.get("probe", {})
            result_data = result.get("result", {})
            resolvers   = probe.get("resolvers", [])
            node_ip     = resolvers[0] if resolvers and resolvers[0] != "private" else ""
            target_ip   = result_data.get("resolvedAddress", "")
            http_code   = result_data.get("statusCode")
            if self._is_blocked_ip(target_ip):
                status = DomainStatus.BLOCKED
            elif not target_ip or not http_code:
                status = DomainStatus.TIMEOUT
            elif 200 <= http_code < 400 or http_code == 403:
                status = DomainStatus.CLEAN
            else:
                status = DomainStatus.WARNING
            nodes.append({
                "isp":              probe.get("network", "Unknown"),
                "asn":              str(probe.get("asn", "")),
                "city":             probe.get("city", "Unknown"),
                "country":          country,
                "node_ip":          node_ip,
                "target_ip":        target_ip,
                "http_code":        http_code,
                "response_time_ms": result_data.get("timings", {}).get("total"),
                "status":           status,
                "error_message":    None,
            })
        return nodes

    def _aggregate(self, domain: str, nodes: List[Dict]) -> Dict:
        counts = {"clean": 0, "blocked": 0, "timeout": 0, "warning": 0}
        for n in nodes:
            s = n.get("status")
            if s == DomainStatus.CLEAN:    counts["clean"]   += 1
            elif s == DomainStatus.BLOCKED:  counts["blocked"]  += 1
            elif s == DomainStatus.TIMEOUT:  counts["timeout"]  += 1
            elif s == DomainStatus.WARNING:  counts["warning"]  += 1
        t = len(nodes)
        if t == 0:                        overall = DomainStatus.API_ERROR
        elif counts["clean"]   == t:     overall = DomainStatus.CLEAN
        elif counts["blocked"] == t:     overall = DomainStatus.BLOCKED
        elif counts["timeout"] == t:     overall = DomainStatus.TIMEOUT
        elif counts["warning"] == t:     overall = DomainStatus.WARNING
        else:                             overall = DomainStatus.PARTIAL
        return {"domain": domain, "status": overall, "nodes": nodes,
                "error": None, "error_analysis": self._analyze(overall, nodes)}

    def _analyze(self, status: DomainStatus, nodes: List[Dict]) -> str:
        if status == DomainStatus.CLEAN:   return "正常連通"
        if status == DomainStatus.BLOCKED:
            ips = {n["target_ip"] for n in nodes if n.get("status") == DomainStatus.BLOCKED}
            return f"DNS 污染 - 封鎖 IP: {', '.join(ips)}"
        if status == DomainStatus.TIMEOUT: return "完全超時"
        if status == DomainStatus.WARNING:
            codes = {str(n["http_code"]) for n in nodes if n.get("http_code")}
            return f"服務異常 - HTTP: {', '.join(codes)}"
        if status == DomainStatus.PARTIAL:
            s = {}
            for n in nodes:
                k = n.get("status", DomainStatus.API_ERROR)
                k = k.value if hasattr(k, "value") else str(k)
                s[k] = s.get(k, 0) + 1
            return f"部分異常: {s}"
        return "API 錯誤"

    async def check_single_domain(
        self, client: httpx.AsyncClient, domain: str
    ) -> Dict:
        from .node_pool import NodePoolManager
        all_nodes, all_errors, api_calls = [], [], 0

        for country in self.target_countries:
            try:
                node_locations = []
                try:
                    npm = NodePoolManager()
                    node_locations = npm.get_country_nodes_for_measurement(
                        country, limit=settings.nodes_per_country
                    )
                except Exception:
                    pass

                if node_locations:
                    payload = {
                        "type": "dns", "target": domain,
                        "limit": settings.nodes_per_country,
                        "locations": node_locations,
                        "measurementOptions": {"query": {"type": "A"}},
                    }
                else:
                    payload = {
                        "type": "dns", "target": domain,
                        "limit": settings.nodes_per_country,
                        "locations": [{"country": country}],
                        "measurementOptions": {"query": {"type": "A"}},
                    }

                r = await client.post(
                    f"{self.api_url}/measurements",
                    json=payload, headers=self.headers, timeout=30.0
                )
                api_calls += 1

                if r.status_code != 202:
                    if r.status_code == 401:
                        err_msg = f"{country}: HTTP 401 — Token 無效或未設定"
                    elif r.status_code == 429 or r.status_code >= 500:
                        wait = settings.api_quota_wait_on_error
                        print(f"   ⏸️  API {r.status_code}，等待 {wait}s ...")
                        await asyncio.sleep(wait)
                        err_msg = f"{country}: HTTP {r.status_code} — 額度耗盡或伺服器錯誤"
                    else:
                        err_msg = f"{country}: HTTP {r.status_code} — {r.text[:200]}"
                    print(f"   ❌ {err_msg}")
                    all_errors.append(err_msg)
                    continue

                measure_id = r.json().get("id")
                if not measure_id:
                    all_errors.append(f"{country}: no measurement id")
                    continue

                await asyncio.sleep(5)
                r2 = await client.get(
                    f"{self.api_url}/measurements/{measure_id}",
                    headers=self.headers, timeout=30.0
                )
                api_calls += 1

                if r2.status_code == 200:
                    all_nodes.extend(self._parse_results_dns(r2.json(), country))
                else:
                    all_errors.append(f"{country}: get results HTTP {r2.status_code}")

            except Exception as e:
                all_errors.append(f"{country}: {e}")

        if not all_nodes:
            err = "; ".join(all_errors) or "All countries failed"
            print(f"   ❌ 域名 {domain} 全部失敗: {err}")
            return {
                "domain": domain, "status": DomainStatus.API_ERROR,
                "error": err, "error_analysis": err,
                "nodes": [], "api_calls": api_calls,
            }

        result = self._aggregate(domain, all_nodes)
        result["api_calls"] = api_calls
        return result


def save_single_result(
    db: Session,
    batch_id: int,
    result: Dict,
    zone_manager: ZoneManager,
    check_duration_ms: int = None,
) -> Dict:
    """即時儲存單個域名結果（V5：加入 check_duration_ms）"""
    domain_name = result["domain"]
    status      = result["status"]

    rec = db.query(Domain).filter(Domain.domain == domain_name).first()
    if not rec:
        rec = Domain(domain=domain_name, zone=DomainZone.PENDING)
        db.add(rec)
        db.flush()

    previous_zone = rec.zone
    zone_changed, new_zone = zone_manager.update_domain_status(
        domain_name, status, batch_id
    )

    dr = DomainResult(
        batch_id          = batch_id,
        domain_id         = rec.domain_id,
        domain            = domain_name,
        overall_status    = status,
        previous_zone     = previous_zone,
        new_zone          = new_zone if zone_changed else previous_zone,
        zone_changed      = zone_changed,
        test_date         = datetime.utcnow(),
        error_message     = result.get("error_analysis", ""),
        check_duration_ms = check_duration_ms,
    )
    db.add(dr)
    db.flush()

    for node in result.get("nodes", []):
        db.add(NodeDetail(
            result_id        = dr.result_id,
            node_isp         = node.get("isp"),
            node_asn         = node.get("asn"),
            node_city        = node.get("city"),
            node_country     = node.get("country", "ID"),
            node_ip          = node.get("node_ip"),
            target_ip        = node.get("target_ip"),
            status           = node.get("status"),
            http_code        = node.get("http_code"),
            response_time_ms = node.get("response_time_ms"),
            error_message    = node.get("error_message"),
        ))
    db.commit()
    return {"zone_changed": zone_changed, "new_zone": new_zone}


async def run_cycle_check(
    domains: List[str],
    cycle_id: int,
    cycle_type: CycleType,
    iteration: int
) -> int:
    """執行循環檢測（V5：記錄 check_duration_ms / api_calls_used）"""
    # 在迴圈開始前一次性 import，避免每次迭代重複 import
    from .node_pool import _isp_priority

    def _get_top(isp: str):
        rank = _isp_priority(isp or "")
        return f"TOP{rank}" if rank <= 30 else None

    db = SessionLocal()
    try:
        start_time    = datetime.utcnow()
        total_domains = len(domains)
        checker       = GlobalpingChecker()
        cycle_name    = "異常區" if cycle_type == CycleType.ABNORMAL_CHECK else "正常區"

        async with httpx.AsyncClient() as client:
            limits = await checker.check_api_limits(client)
            if limits:
                remaining = (
                    limits.get('rateLimit', {})
                    .get('measurements', {}).get('create', {}).get('remaining', 0)
                )
                required = checker.calculate_required_calls(total_domains)
                print(f"📊 API 額度: {remaining} 剩餘 / 需要 {required}")
                if remaining < required:
                    max_d = remaining // (len(checker.target_countries) * 2)
                    if max_d == 0:
                        print("❌ 額度不足，跳過")
                        return None
                    domains       = domains[:max_d]
                    total_domains = len(domains)
                    print(f"⚠️  額度不足，本次只檢測 {total_domains} 個")

        batch = TestBatch(
            cycle_id=cycle_id, cycle_type=cycle_type,
            iteration=iteration, test_date=start_time,
            total_domains=total_domains,
            notes=f"{cycle_name} 第 {iteration} 次 (進行中...)"
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        batch_id = batch.batch_id

        stats = {"clean": 0, "blocked": 0, "timeout": 0,
                 "warning": 0, "partial": 0, "api_error": 0}
        moved_to_normal = moved_to_abnormal = total_api_calls = 0
        zm = ZoneManager(db)

        _check_progress.update({
            "running": True, "current_domain": None,
            "current_index": 0, "total_domains": total_domains,
            "started_at": start_time.isoformat(),
            "cycle_type": cycle_type.value,
            "stats": stats.copy(), "recent_results": [],
        })

        async with httpx.AsyncClient() as client:
            for i, domain in enumerate(domains):
                # 暫停檢查
                global _stop_flag
                if _stop_flag:
                    print(f"⏹️  檢測已暫停（完成 {i}/{total_domains} 個）")
                    _stop_flag = False
                    break

                print(f"🔍 [{i+1}/{total_domains}] {domain}")
                _check_progress["current_domain"] = domain
                _check_progress["current_index"]  = i + 1

                t0     = datetime.utcnow()
                result = await checker.check_single_domain(client, domain)
                dur_ms = int((datetime.utcnow() - t0).total_seconds() * 1000)
                total_api_calls += result.get("api_calls", 0)

                status = result["status"]
                nodes  = result.get("nodes", [])

                # 更新進度節點資訊
                if nodes:
                    fn = nodes[0]
                    _check_progress["current_node_isp"]  = fn.get("isp")
                    _check_progress["current_node_city"] = fn.get("city")
                    isp_rank = _isp_priority(fn.get("isp", ""))
                    _check_progress["current_node_top"] = f"TOP{isp_rank}" if isp_rank <= 30 else None

                # 更新統計
                key = status.value.lower() if hasattr(status, "value") else "api_error"
                if key in stats:
                    stats[key] += 1
                else:
                    stats["api_error"] += 1

                # 判斷 test type（DNS 模式：payload type 為 dns；HTTP 模式：http）
                # checker 目前只使用 DNS 模式，未來 HTTP 模式可從 payload 取得
                test_type = "dns"  # V5 預設 DNS 模式

                # 建立每個節點的摘要（最多顯示 5 個，依 isp_rank 排序）
                # 依 isp_rank 排序節點（TOP1 優先）
                sorted_nodes = sorted(
                    nodes,
                    key=lambda n: _isp_priority(n.get("isp") or "")
                )

                node_summaries = [
                    {
                        "isp":    n.get("isp"),
                        "city":   n.get("city"),
                        "status": n.get("status").value if hasattr(n.get("status"), "value") else str(n.get("status", "")),
                        "top":    _get_top(n.get("isp")),
                    }
                    for n in sorted_nodes[:5]
                ]

                entry = {
                    "domain": domain,
                    "status": status.value if hasattr(status, "value") else str(status),
                    "error":  result.get("error_analysis", ""),
                    "time":   datetime.utcnow().isoformat() + "Z",
                    "dur_ms": dur_ms,
                    "isp":    nodes[0].get("isp") if nodes else None,
                    "city":   nodes[0].get("city") if nodes else None,
                    "top":    _check_progress.get("current_node_top"),
                    "type":   test_type,
                    "http_code": nodes[0].get("http_code") if nodes else None,
                    "nodes":  node_summaries,
                }
                _check_progress["last_result"] = entry
                # 儲存全部結果（前端自行分頁），最新的在前
                _check_progress["recent_results"] = (
                    [entry] + _check_progress["recent_results"]
                )
                _check_progress["stats"] = stats.copy()

                save_r = save_single_result(db, batch_id, result, zm, dur_ms)
                if save_r["zone_changed"]:
                    if save_r["new_zone"] == DomainZone.NORMAL:
                        moved_to_normal += 1
                    elif save_r["new_zone"] == DomainZone.ABNORMAL:
                        moved_to_abnormal += 1

                if (i + 1) % 10 == 0 or (i + 1) == total_domains:
                    batch.clean_count     = stats["clean"]
                    batch.blocked_count   = stats["blocked"]
                    batch.timeout_count   = stats["timeout"]
                    batch.warning_count   = stats["warning"]
                    batch.partial_count   = stats["partial"]
                    batch.api_error_count = stats["api_error"]
                    batch.moved_to_normal   = moved_to_normal
                    batch.moved_to_abnormal = moved_to_abnormal
                    batch.api_calls_used    = total_api_calls
                    batch.duration_seconds  = (datetime.utcnow() - start_time).total_seconds()
                    batch.notes = f"{cycle_name} 第 {iteration} 次 ({i+1}/{total_domains})"
                    db.commit()

                if (i + 1) % 30 == 0 and (i + 1) < total_domains:
                    print("⏸️  批次休息 60 秒...")
                    await asyncio.sleep(60)
                else:
                    await asyncio.sleep(8)

        # 最終更新
        _stop_flag = False
        batch.duration_seconds  = (datetime.utcnow() - start_time).total_seconds()
        batch.api_calls_used    = total_api_calls
        batch.notes = f"{cycle_name} 第 {iteration} 次 (完成)"
        db.commit()

        print(f"\n✅ 批次 #{batch_id} 完成")
        print(f"   正常:{stats['clean']} 封鎖:{stats['blocked']} "
              f"超時:{stats['timeout']} 警告:{stats['warning']} "
              f"部分:{stats['partial']} 錯誤:{stats['api_error']}")
        print(f"   API 調用: {total_api_calls} | 耗時: {batch.duration_seconds:.1f}s")

        _check_progress["running"] = False
        _check_progress["stats"]   = stats.copy()
        return batch_id

    except Exception as e:
        print(f"❌ 檢測錯誤: {e}")
        _check_progress["running"] = False
        db.rollback()
        raise
    finally:
        db.close()
