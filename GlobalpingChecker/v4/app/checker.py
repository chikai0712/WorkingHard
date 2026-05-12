"""
GlobalpingChecker V4 - Domain Checker
使用 Globalping API 檢測域名狀態
"""
import asyncio
import httpx
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from .config import get_settings
from .database import (
    TestBatch, DomainResult, NodeDetail, DomainHistory, SchedulerLog,
    DomainStatus, SessionLocal
)

settings = get_settings()


class GlobalpingChecker:
    """Globalping API 域名檢測器"""
    
    # 已知的 DNS 污染 IP
    BLOCKED_IPS = {
        "36.86.63.185",
        "10.0.0.0/8",  # 私有 IP 範圍
    }
    
    def __init__(self):
        self.api_url = settings.globalping_api_url
        self.token = settings.globalping_token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        
    async def check_single_domain(self, client: httpx.AsyncClient, domain: str) -> Dict:
        """檢測單個域名"""
        try:
            # 建立測量請求
            payload = {
                "type": "http",
                "target": domain,
                "limit": 3,
                "locations": [{"country": "ID"}]
            }
            
            # 發送 POST 請求建立測量
            response = await client.post(
                f"{self.api_url}/measurements",
                json=payload,
                headers=self.headers,
                timeout=30.0
            )
            
            if response.status_code != 202:
                return {
                    "domain": domain,
                    "status": DomainStatus.API_ERROR,
                    "error": f"API returned {response.status_code}",
                    "nodes": []
                }
            
            data = response.json()
            measure_id = data.get("id")
            
            if not measure_id:
                return {
                    "domain": domain,
                    "status": DomainStatus.API_ERROR,
                    "error": "No measurement ID returned",
                    "nodes": []
                }
            
            # 等待測量完成
            await asyncio.sleep(8)
            
            # 獲取測量結果
            result_response = await client.get(
                f"{self.api_url}/measurements/{measure_id}",
                headers=self.headers,
                timeout=30.0
            )
            
            if result_response.status_code != 200:
                return {
                    "domain": domain,
                    "status": DomainStatus.API_ERROR,
                    "error": f"Failed to get results: {result_response.status_code}",
                    "nodes": []
                }
            
            result_data = result_response.json()
            return self._parse_results(domain, result_data)
            
        except httpx.TimeoutException:
            return {
                "domain": domain,
                "status": DomainStatus.API_ERROR,
                "error": "Request timeout",
                "nodes": []
            }
        except Exception as e:
            return {
                "domain": domain,
                "status": DomainStatus.API_ERROR,
                "error": str(e),
                "nodes": []
            }
    
    def _parse_results(self, domain: str, data: Dict) -> Dict:
        """解析 Globalping API 結果"""
        nodes = []
        status_counts = {
            "clean": 0,
            "blocked": 0,
            "timeout": 0,
            "warning": 0
        }
        
        for result in data.get("results", []):
            probe = result.get("probe", {})
            result_data = result.get("result", {})
            
            # 節點信息
            node = {
                "isp": probe.get("network", "Unknown"),
                "asn": str(probe.get("asn", "")),
                "city": probe.get("city", "Unknown"),
                "country": probe.get("country", "ID"),
                "node_ip": "",
                "target_ip": result_data.get("resolvedAddress", ""),
                "http_code": result_data.get("statusCode"),
                "response_time_ms": result_data.get("timings", {}).get("total"),
                "error_message": None
            }
            
            # 獲取節點 IP（resolver）
            resolvers = probe.get("resolvers", [])
            if resolvers:
                node["node_ip"] = resolvers[0] if resolvers[0] != "private" else "private"
            
            # 判斷節點狀態
            target_ip = node["target_ip"]
            http_code = node["http_code"]
            
            if self._is_blocked_ip(target_ip):
                node["status"] = DomainStatus.BLOCKED
                status_counts["blocked"] += 1
            elif not target_ip or http_code == 0 or http_code is None:
                node["status"] = DomainStatus.TIMEOUT
                status_counts["timeout"] += 1
            elif http_code and (200 <= http_code < 400 or http_code == 403):
                node["status"] = DomainStatus.CLEAN
                status_counts["clean"] += 1
            else:
                node["status"] = DomainStatus.WARNING
                status_counts["warning"] += 1
            
            nodes.append(node)
        
        # 判斷整體狀態
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
        
        return {
            "domain": domain,
            "status": overall_status,
            "nodes": nodes,
            "error": None
        }
    
    def _is_blocked_ip(self, ip: str) -> bool:
        """檢查是否為已知的污染 IP"""
        if not ip:
            return False
        if ip == "36.86.63.185":
            return True
        if ip.startswith("10."):
            return True
        return False
    
    async def check_domains(self, domains: List[str], batch_size: int = 30, 
                           delay: float = 8.0, batch_delay: float = 60.0) -> Tuple[TestBatch, List[Dict]]:
        """批量檢測域名"""
        start_time = datetime.utcnow()
        results = []
        
        # 統計
        stats = {
            "clean": 0,
            "blocked": 0,
            "timeout": 0,
            "warning": 0,
            "partial": 0,
            "api_error": 0
        }
        
        async with httpx.AsyncClient() as client:
            for i, domain in enumerate(domains):
                print(f"🔍 檢測 [{i+1}/{len(domains)}]: {domain}")
                
                result = await self.check_single_domain(client, domain)
                results.append(result)
                
                # 更新統計
                status = result["status"]
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
                
                # 延遲控制
                if (i + 1) % batch_size == 0 and i + 1 < len(domains):
                    print(f"⏸️  批次休息 {batch_delay} 秒...")
                    await asyncio.sleep(batch_delay)
                else:
                    await asyncio.sleep(delay)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # 建立批次記錄
        batch = TestBatch(
            test_date=start_time,
            total_domains=len(domains),
            clean_count=stats["clean"],
            blocked_count=stats["blocked"],
            timeout_count=stats["timeout"],
            warning_count=stats["warning"],
            partial_count=stats["partial"],
            api_error_count=stats["api_error"],
            duration_seconds=duration
        )
        
        return batch, results


def save_results_to_db(db: Session, batch: TestBatch, results: List[Dict], 
                       notes: str = "", is_scheduled: bool = False) -> int:
    """保存檢測結果到資料庫"""
    batch.notes = notes
    batch.is_scheduled = is_scheduled
    db.add(batch)
    db.flush()
    
    batch_id = batch.batch_id
    
    # 獲取上一次的域名狀態（用於歷史追蹤）
    previous_statuses = {}
    last_batch = db.query(TestBatch).filter(
        TestBatch.batch_id < batch_id
    ).order_by(TestBatch.batch_id.desc()).first()
    
    if last_batch:
        prev_results = db.query(DomainResult).filter(
            DomainResult.batch_id == last_batch.batch_id
        ).all()
        for pr in prev_results:
            previous_statuses[pr.domain] = pr.overall_status
    
    # 保存每個域名的結果
    for result in results:
        domain_result = DomainResult(
            batch_id=batch_id,
            domain=result["domain"],
            overall_status=result["status"].value if isinstance(result["status"], DomainStatus) else result["status"],
            test_date=batch.test_date
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
                status=node.get("status").value if isinstance(node.get("status"), DomainStatus) else node.get("status"),
                http_code=node.get("http_code"),
                response_time_ms=node.get("response_time_ms"),
                error_message=node.get("error_message")
            )
            db.add(node_detail)
        
        # 檢查狀態變化，記錄歷史
        current_status = result["status"].value if isinstance(result["status"], DomainStatus) else result["status"]
        prev_status = previous_statuses.get(result["domain"])
        
        if prev_status and prev_status != current_status:
            history = DomainHistory(
                domain=result["domain"],
                previous_status=prev_status,
                current_status=current_status,
                changed_at=batch.test_date,
                batch_id=batch_id,
                notes=f"狀態從 {prev_status} 變為 {current_status}"
            )
            db.add(history)
    
    db.commit()
    return batch_id


async def run_check(domains_file: str, notes: str = "", is_scheduled: bool = False) -> int:
    """執行檢測並保存結果"""
    # 讀取域名列表
    with open(domains_file, 'r', encoding='utf-8') as f:
        domains = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith('#') and '.' in line
        ]
    
    if not domains:
        print("❌ 沒有找到有效的域名")
        return -1
    
    print(f"📋 載入 {len(domains)} 個域名")
    
    # 執行檢測
    checker = GlobalpingChecker()
    batch, results = await checker.check_domains(domains)
    
    # 保存到資料庫
    db = SessionLocal()
    try:
        batch_id = save_results_to_db(db, batch, results, notes, is_scheduled)
        print(f"\n✅ 檢測完成！批次 ID: {batch_id}")
        print(f"   正常: {batch.clean_count} | 封鎖: {batch.blocked_count} | 超時: {batch.timeout_count}")
        print(f"   警告: {batch.warning_count} | 部分: {batch.partial_count} | 錯誤: {batch.api_error_count}")
        return batch_id
    finally:
        db.close()
