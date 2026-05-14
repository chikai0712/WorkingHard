"""
GlobalpingChecker V4.1 - Node Validator
節點 IP 驗證器 - 使用 IP 地理位置 API 驗證節點是否屬於指定國家
"""
import asyncio
import httpx
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import NodeDetail, DomainResult


class NodeValidator:
    """節點 IP 驗證器"""
    
    # 免費 IP 地理位置 API
    IP_API_URL = "http://ip-api.com/json/{ip}?fields=status,country,countryCode,region,city,isp,org,as,query"
    
    # 備用 API
    IPINFO_URL = "https://ipinfo.io/{ip}/json"
    
    def __init__(self):
        self.cache: Dict[str, Dict] = {}  # IP 查詢緩存
    
    async def validate_ip(self, ip: str, expected_country: str = "ID") -> Dict:
        """
        驗證單個 IP 的地理位置。

        參數：
            ip               : 要驗證的 IP 地址
            expected_country : 期望的國家代碼（ISO 3166-1 alpha-2），預設 "ID"（印尼）

        返回: {
            "ip": str,
            "country": str,
            "country_code": str,
            "city": str,
            "isp": str,
            "asn": str,
            "is_valid": bool,  # 是否屬於 expected_country
            "source": str
        }
        """
        if not ip or ip == "private" or ip.startswith("10.") or ip.startswith("192.168."):
            return {
                "ip": ip,
                "country": "Private",
                "country_code": "N/A",
                "city": "N/A",
                "isp": "Private Network",
                "asn": "N/A",
                "is_valid": False,
                "source": "local"
            }

        # 檢查緩存（以 ip+country 為 key，避免同 IP 用於不同國家時誤判）
        cache_key = f"{ip}:{expected_country}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.IP_API_URL.format(ip=ip),
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        result = {
                            "ip": ip,
                            "country": data.get("country", "Unknown"),
                            "country_code": data.get("countryCode", "??"),
                            "city": data.get("city", "Unknown"),
                            "isp": data.get("isp", "Unknown"),
                            "asn": data.get("as", "").split()[0] if data.get("as") else "Unknown",
                            "is_valid": data.get("countryCode") == expected_country,
                            "source": "ip-api.com"
                        }
                        self.cache[cache_key] = result
                        return result
        except Exception as e:
            print(f"⚠️ IP 查詢失敗 ({ip}): {e}")

        # 返回未知結果
        return {
            "ip": ip,
            "country": "Unknown",
            "country_code": "??",
            "city": "Unknown",
            "isp": "Unknown",
            "asn": "Unknown",
            "is_valid": False,
            "source": "error"
        }
    
    async def validate_nodes(self, nodes: List[Dict], delay: float = 0.5) -> List[Dict]:
        """
        批量驗證節點 IP
        - 驗證 node_ip（檢測節點 IP）
        - 驗證 target_ip（解析目標 IP）
        """
        results = []
        
        for node in nodes:
            node_result = dict(node)
            
            # 驗證節點 IP
            node_ip = node.get("node_ip")
            if node_ip and node_ip != "private":
                node_validation = await self.validate_ip(node_ip)
                node_result["node_validation"] = node_validation
                await asyncio.sleep(delay)  # 避免 API 限流
            else:
                node_result["node_validation"] = None
            
            # 驗證目標 IP
            target_ip = node.get("target_ip")
            if target_ip:
                target_validation = await self.validate_ip(target_ip)
                node_result["target_validation"] = target_validation
                await asyncio.sleep(delay)
            else:
                node_result["target_validation"] = None
            
            results.append(node_result)
        
        return results
    
    async def validate_batch_nodes(
        self, 
        db: Session, 
        batch_id: int,
        limit: int = 100
    ) -> Dict:
        """
        驗證批次中的所有節點
        返回驗證統計和所有節點詳情
        """
        # 獲取批次的節點
        nodes = db.query(NodeDetail).join(DomainResult).filter(
            DomainResult.batch_id == batch_id
        ).limit(limit).all()
        
        stats = {
            "total_nodes": len(nodes),
            "valid_nodes": 0,
            "invalid_nodes": 0,
            "unknown_nodes": 0,
            "private_nodes": 0,
            "countries": {},
            "details": []
        }
        
        for node in nodes:
            # 優先使用 target_ip，如果沒有則使用 node_ip
            ip_to_validate = node.target_ip if node.target_ip else node.node_ip
            
            # 如果是 private IP，直接使用數據庫中的信息
            if not ip_to_validate or ip_to_validate == "private":
                stats["private_nodes"] += 1
                stats["details"].append({
                    "node_ip": node.node_ip or "N/A",
                    "target_ip": node.target_ip or "N/A",
                    "expected_country": node.node_country or "ID",
                    "actual_country": node.node_country or "ID",
                    "actual_country_name": node.node_country or "Unknown",
                    "city": node.node_city or "Unknown",
                    "isp": node.node_isp or "Unknown",
                    "asn": node.node_asn or "Unknown",
                    "is_valid": True,  # 假設數據庫中的是正確的
                    "source": "database"
                })
            else:
                # 驗證 IP，使用節點記錄中的國家代碼
                expected = node.node_country or "ID"
                validation = await self.validate_ip(ip_to_validate, expected_country=expected)
                
                if validation["is_valid"]:
                    stats["valid_nodes"] += 1
                elif validation["country_code"] == "??":
                    stats["unknown_nodes"] += 1
                else:
                    stats["invalid_nodes"] += 1
                
                # 統計國家
                country = validation["country_code"]
                stats["countries"][country] = stats["countries"].get(country, 0) + 1
                
                stats["details"].append({
                    "node_ip": node.node_ip or "N/A",
                    "target_ip": node.target_ip or "N/A",
                    "expected_country": expected,
                    "actual_country": validation["country_code"],
                    "actual_country_name": validation["country"],
                    "city": validation["city"],
                    "isp": validation["isp"],
                    "asn": validation["asn"],
                    "is_valid": validation["is_valid"],
                    "source": validation["source"]
                })

                await asyncio.sleep(0.5)  # 避免 API 限流

        return stats


async def validate_single_ip(ip: str, expected_country: str = "ID") -> Dict:
    """便捷函數：驗證單個 IP"""
    validator = NodeValidator()
    return await validator.validate_ip(ip, expected_country=expected_country)
