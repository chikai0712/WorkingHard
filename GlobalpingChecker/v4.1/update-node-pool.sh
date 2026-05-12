#!/bin/bash

# V4.1 節點池功能更新腳本
# 在 AWS EC2 終端機上執行此腳本

set -e

echo "========================================"
echo "🚀 GlobalpingChecker V4.1 節點池更新"
echo "========================================"
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="$HOME/globalping-v4.1"
BACKUP_DIR="$HOME/globalping-v4.1-backup-nodepool-$(date +%Y%m%d-%H%M%S)"

echo -e "${YELLOW}步驟 1/5: 備份當前版本${NC}"
cp -r "$PROJECT_DIR" "$BACKUP_DIR"
echo -e "${GREEN}✅ 備份完成: $BACKUP_DIR${NC}"
echo ""

echo -e "${YELLOW}步驟 2/5: 停止服務${NC}"
cd "$PROJECT_DIR"
docker-compose down
echo -e "${GREEN}✅ 服務已停止${NC}"
echo ""

echo -e "${YELLOW}步驟 3/5: 更新代碼${NC}"

# 創建 node_pool.py
cat > "$PROJECT_DIR/app/node_pool.py" << 'NODEPOOL_EOF'
"""
GlobalpingChecker V4.1 - Node Pool Manager
管理和驗證節點池
"""
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean

from .database import Base, get_db_session
from .node_validator import NodeValidator
from .config import get_settings

settings = get_settings()


class NodePool(Base):
    """節點池數據表"""
    __tablename__ = "node_pool"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String, unique=True, index=True)
    node_ip = Column(String)
    country = Column(String, index=True)
    country_name = Column(String)
    city = Column(String)
    isp = Column(String)
    asn = Column(String)
    is_active = Column(Boolean, default=True)
    last_verified = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)


class NodePoolManager:
    """節點池管理器"""
    
    def __init__(self):
        self.api_url = settings.globalping_api_url
        self.token = settings.globalping_token
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.validator = NodeValidator()
        self.target_countries = settings.target_country_list
    
    async def initialize_node_pool(self):
        """初始化節點池"""
        print("🔍 初始化節點池...")
        
        for country in self.target_countries:
            print(f"   獲取 {country} 節點...")
            nodes = await self.fetch_country_nodes(country)
            
            if nodes:
                await self.save_nodes_to_db(nodes, country)
                print(f"   ✅ {country}: 已保存 {len(nodes)} 個節點")
            else:
                print(f"   ⚠️  {country}: 未找到可用節點")
    
    async def fetch_country_nodes(self, country: str) -> List[Dict]:
        """從 Globalping 獲取指定國家的所有節點"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/probes",
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    print(f"      ❌ API 錯誤: {response.status_code}")
                    return []
                
                all_probes = response.json()
                country_nodes = []
                
                for probe in all_probes:
                    if probe.get("country") == country and probe.get("status") == "ready":
                        node_ip = ""
                        resolvers = probe.get("resolvers", [])
                        if resolvers:
                            node_ip = resolvers[0] if resolvers[0] != "private" else "private"
                        
                        if node_ip and node_ip != "private":
                            ip_validation = await self.validator.validate_ip(node_ip)
                            if ip_validation["country_code"] != country:
                                continue
                        
                        node = {
                            "node_id": probe.get("id"),
                            "node_ip": node_ip,
                            "country": country,
                            "country_name": probe.get("country"),
                            "city": probe.get("city", "Unknown"),
                            "isp": probe.get("network", "Unknown"),
                            "asn": str(probe.get("asn", "")),
                        }
                        country_nodes.append(node)
                
                return country_nodes
                
        except Exception as e:
            print(f"      ❌ 獲取節點失敗: {e}")
            return []
    
    async def save_nodes_to_db(self, nodes: List[Dict], country: str):
        """保存節點到資料庫"""
        from .database import SessionLocal
        db = SessionLocal()
        try:
            for node in nodes:
                existing = db.query(NodePool).filter(
                    NodePool.node_id == node["node_id"]
                ).first()
                
                if existing:
                    existing.last_verified = datetime.now()
                    existing.is_active = True
                else:
                    db_node = NodePool(
                        node_id=node["node_id"],
                        node_ip=node["node_ip"],
                        country=node["country"],
                        country_name=node["country_name"],
                        city=node["city"],
                        isp=node["isp"],
                        asn=node["asn"],
                        last_verified=datetime.now()
                    )
                    db.add(db_node)
            
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"      ❌ 保存節點失敗: {e}")
        finally:
            db.close()
    
    def get_country_nodes(self, country: str, limit: int = 3) -> List[str]:
        """從資料庫獲取指定國家的節點 ID"""
        from .database import SessionLocal
        db = SessionLocal()
        try:
            nodes = db.query(NodePool).filter(
                NodePool.country == country,
                NodePool.is_active == True
            ).limit(limit).all()
            
            return [node.node_id for node in nodes]
        finally:
            db.close()
    
    def get_node_pool_stats(self) -> Dict:
        """獲取節點池統計"""
        from .database import SessionLocal
        db = SessionLocal()
        try:
            stats = {}
            for country in self.target_countries:
                count = db.query(NodePool).filter(
                    NodePool.country == country,
                    NodePool.is_active == True
                ).count()
                stats[country] = count
            
            return stats
        finally:
            db.close()
NODEPOOL_EOF

echo -e "${GREEN}✅ node_pool.py 已更新${NC}"
echo ""

echo -e "${YELLOW}步驟 4/5: 重新構建並啟動服務${NC}"
docker-compose build
docker-compose up -d
echo -e "${GREEN}✅ 服務已啟動${NC}"
echo ""

echo -e "${YELLOW}步驟 5/5: 等待服務啟動${NC}"
sleep 5
docker-compose ps
echo ""

echo -e "${GREEN}========================================"
echo "✅ 節點池功能更新完成！"
echo "========================================${NC}"
echo ""
echo "📊 查看日誌："
echo "   docker-compose logs -f"
echo ""
echo "🔍 查看節點池初始化："
echo "   docker-compose logs | grep '節點池'"
echo ""
