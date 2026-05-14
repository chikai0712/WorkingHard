"""
GlobalpingChecker V4.1 - Zone Manager
域名區域管理器 - 管理正常區/異常區的域名分配
"""
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import (
    Domain, DomainZone, DomainStatus, DomainZoneHistory,
    DomainResult, TestBatch, CheckCycle, CycleType, SystemLog
)


class ZoneManager:
    """域名區域管理器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def initialize_domains(self, domains: List[str]) -> Dict[str, int]:
        """
        初始化域名列表
        - 新域名加入 PENDING 區
        - 返回統計信息
        """
        stats = {"added": 0, "existing": 0}
        
        for domain_name in domains:
            domain_name = domain_name.strip()
            if not domain_name or domain_name.startswith('#'):
                continue
            
            existing = self.db.query(Domain).filter(Domain.domain == domain_name).first()
            if existing:
                stats["existing"] += 1
            else:
                domain = Domain(
                    domain=domain_name,
                    zone=DomainZone.PENDING,
                    created_at=datetime.utcnow()
                )
                self.db.add(domain)
                stats["added"] += 1
        
        self.db.commit()
        return stats
    
    def get_domains_by_zone(self, zone: DomainZone) -> List[Domain]:
        """獲取指定區域的所有域名"""
        return self.db.query(Domain).filter(Domain.zone == zone).all()
    
    def get_domain_names_by_zone(self, zone: DomainZone) -> List[str]:
        """獲取指定區域的域名列表（僅名稱）"""
        domains = self.db.query(Domain.domain).filter(Domain.zone == zone).all()
        return [d[0] for d in domains]
    
    def get_zone_stats(self) -> Dict[str, int]:
        """獲取各區域的域名統計"""
        stats = {}
        for zone in DomainZone:
            count = self.db.query(func.count(Domain.domain_id)).filter(
                Domain.zone == zone
            ).scalar()
            stats[zone.value] = count
        return stats
    
    def move_domain_to_zone(
        self, 
        domain_name: str, 
        new_zone: DomainZone, 
        reason: str,
        batch_id: Optional[int] = None
    ) -> bool:
        """
        將域名移動到指定區域
        - 記錄變更歷史
        """
        domain = self.db.query(Domain).filter(Domain.domain == domain_name).first()
        if not domain:
            return False
        
        old_zone = domain.zone
        if old_zone == new_zone:
            return False  # 沒有變化
        
        # 更新域名區域
        domain.zone = new_zone
        domain.updated_at = datetime.utcnow()
        
        # 記錄歷史
        history = DomainZoneHistory(
            domain_id=domain.domain_id,
            previous_zone=old_zone,
            new_zone=new_zone,
            reason=reason,
            batch_id=batch_id,
            changed_at=datetime.utcnow()
        )
        self.db.add(history)
        self.db.commit()
        
        return True
    
    def update_domain_status(
        self,
        domain_name: str,
        status: DomainStatus,
        batch_id: Optional[int] = None
    ) -> Tuple[bool, Optional[DomainZone]]:
        """
        更新域名狀態並決定是否需要移動區域
        返回: (是否移動, 新區域)
        """
        domain = self.db.query(Domain).filter(Domain.domain == domain_name).first()
        if not domain:
            return False, None
        
        old_zone = domain.zone
        new_zone = None
        zone_changed = False
        
        # 更新狀態
        domain.current_status = status
        domain.last_check_time = datetime.utcnow()
        domain.total_checks += 1
        
        # 判斷是否為正常狀態
        is_normal = (status == DomainStatus.CLEAN)
        
        if is_normal:
            domain.consecutive_normal += 1
            domain.consecutive_abnormal = 0
            
            # 如果在異常區且連續正常，移到正常區
            if old_zone == DomainZone.ABNORMAL:
                new_zone = DomainZone.NORMAL
                zone_changed = True
                reason = f"連續正常 {domain.consecutive_normal} 次，從異常區移至正常區"
            # 如果在待分類區，移到正常區
            elif old_zone == DomainZone.PENDING:
                new_zone = DomainZone.NORMAL
                zone_changed = True
                reason = "首次檢測正常，移至正常區"
        else:
            domain.consecutive_abnormal += 1
            domain.consecutive_normal = 0
            
            # 如果在正常區且異常，移到異常區
            if old_zone == DomainZone.NORMAL:
                new_zone = DomainZone.ABNORMAL
                zone_changed = True
                reason = f"檢測異常 ({status.value})，從正常區移至異常區"
            # 如果在待分類區，移到異常區
            elif old_zone == DomainZone.PENDING:
                new_zone = DomainZone.ABNORMAL
                zone_changed = True
                reason = f"首次檢測異常 ({status.value})，移至異常區"
        
        # 執行區域移動
        if zone_changed and new_zone:
            self.move_domain_to_zone(domain_name, new_zone, reason, batch_id)
        
        self.db.commit()
        return zone_changed, new_zone
    
    def process_batch_results(
        self,
        batch_id: int,
        results: List[Dict]
    ) -> Dict[str, int]:
        """
        處理批次檢測結果
        - 更新域名狀態
        - 移動域名到對應區域
        - 返回統計
        """
        stats = {
            "total": len(results),
            "normal": 0,
            "abnormal": 0,
            "moved_to_normal": 0,
            "moved_to_abnormal": 0
        }
        
        for result in results:
            domain_name = result["domain"]
            status = result["status"]
            
            if isinstance(status, str):
                status = DomainStatus(status)
            
            is_normal = (status == DomainStatus.CLEAN)
            if is_normal:
                stats["normal"] += 1
            else:
                stats["abnormal"] += 1
            
            # 更新狀態並檢查區域變更
            zone_changed, new_zone = self.update_domain_status(
                domain_name, status, batch_id
            )
            
            if zone_changed:
                if new_zone == DomainZone.NORMAL:
                    stats["moved_to_normal"] += 1
                elif new_zone == DomainZone.ABNORMAL:
                    stats["moved_to_abnormal"] += 1
        
        # 更新批次統計
        batch = self.db.query(TestBatch).filter(TestBatch.batch_id == batch_id).first()
        if batch:
            batch.moved_to_normal = stats["moved_to_normal"]
            batch.moved_to_abnormal = stats["moved_to_abnormal"]
            self.db.commit()
        
        return stats
    
    def get_domains_for_check(self, cycle_type: CycleType) -> List[str]:
        """
        根據循環類型獲取需要檢測的域名
        - ABNORMAL_CHECK: 檢測異常區 + 待分類區
        - NORMAL_CHECK: 檢測正常區（如果正常區為空且有待分類域名，先檢測待分類區）
        """
        if cycle_type == CycleType.ABNORMAL_CHECK:
            # 第一循環：檢測異常區和待分類區
            domains = self.db.query(Domain.domain).filter(
                Domain.zone.in_([DomainZone.ABNORMAL, DomainZone.PENDING])
            ).all()
        else:
            # 第二循環：檢測正常區
            domains = self.db.query(Domain.domain).filter(
                Domain.zone == DomainZone.NORMAL
            ).all()
            
            # 如果正常區為空，檢查是否有待分類的域名（初始化檢測）
            if not domains:
                pending_count = self.db.query(func.count(Domain.domain_id)).filter(
                    Domain.zone == DomainZone.PENDING
                ).scalar()
                
                if pending_count > 0:
                    print(f"📋 正常區為空，先檢測 {pending_count} 個待分類域名")
                    domains = self.db.query(Domain.domain).filter(
                        Domain.zone == DomainZone.PENDING
                    ).all()
        
        return [d[0] for d in domains]
    
    def log_system_event(self, log_type: str, message: str, details: Optional[Dict] = None):
        """記錄系統事件"""
        log = SystemLog(
            log_type=log_type,
            message=message,
            details=json.dumps(details, ensure_ascii=False) if details else None,
            log_time=datetime.utcnow()
        )
        self.db.add(log)
        self.db.commit()
