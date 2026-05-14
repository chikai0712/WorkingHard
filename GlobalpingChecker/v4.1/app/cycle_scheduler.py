"""
GlobalpingChecker V4.1 - Cycle Scheduler
智能循環排程器 - 管理檢測循環和時間排程
"""
import asyncio
from datetime import datetime, time, timedelta
from typing import Optional, Dict, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from .models import (
    CheckCycle, CycleType, CycleSchedule, TestBatch,
    DomainZone, SystemLog
)
from .zone_manager import ZoneManager
from .config import get_settings

settings = get_settings()


class CycleScheduler:
    """智能循環排程器"""
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.scheduler = AsyncIOScheduler()
        self.current_cycle_id: Optional[int] = None
        self.check_callback = None  # 檢測回調函數
        
        # 默認配置
        self.abnormal_check_hour = 1    # AM 1:00 開始異常區檢測
        self.normal_check_hour = 9      # AM 9:00 開始正常區檢測
        self.check_interval = 90        # 檢測間隔（分鐘）
        self.max_iterations = 10        # 第一循環最大檢測次數
    
    def set_check_callback(self, callback):
        """設置檢測回調函數"""
        self.check_callback = callback
    
    def start(self):
        """啟動排程器"""
        # 添加循環切換任務
        # AM 1:00 切換到異常區檢測（第一循環）
        self.scheduler.add_job(
            self._switch_to_abnormal_check,
            CronTrigger(hour=self.abnormal_check_hour, minute=0),
            id="switch_to_abnormal",
            name="切換到異常區檢測",
            replace_existing=True
        )
        
        # AM 9:00 切換到正常區檢測（第二循環）
        self.scheduler.add_job(
            self._switch_to_normal_check,
            CronTrigger(hour=self.normal_check_hour, minute=0),
            id="switch_to_normal",
            name="切換到正常區檢測",
            replace_existing=True
        )
        
        # 添加定期檢測任務
        self.scheduler.add_job(
            self._scheduled_check,
            IntervalTrigger(minutes=self.check_interval),
            id="periodic_check",
            name=f"定期檢測 (每 {self.check_interval} 分鐘)",
            replace_existing=True
        )
        
        self.scheduler.start()
        
        # 初始化當前循環
        self._initialize_current_cycle()
        
        print(f"⏰ V4.1 智能排程器已啟動")
        print(f"   - AM {self.abnormal_check_hour}:00 開始異常區檢測（第一循環）")
        print(f"   - AM {self.normal_check_hour}:00 開始正常區檢測（第二循環）")
        print(f"   - 檢測間隔: {self.check_interval} 分鐘")
    
    def stop(self):
        """停止排程器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("⏰ 排程器已停止")
    
    def _initialize_current_cycle(self):
        """根據當前時間初始化循環"""
        current_hour = datetime.now().hour
        
        db = self.db_session_factory()
        try:
            # 檢查是否有活躍的循環
            active_cycle = db.query(CheckCycle).filter(
                CheckCycle.is_active == True
            ).order_by(CheckCycle.started_at.desc()).first()
            
            if active_cycle:
                self.current_cycle_id = active_cycle.cycle_id
                print(f"📋 恢復現有循環: {active_cycle.cycle_type.value} "
                      f"(第 {active_cycle.cycle_number} 輪, 第 {active_cycle.iteration} 次)")
            else:
                # 根據時間決定循環類型
                if self.abnormal_check_hour <= current_hour < self.normal_check_hour:
                    cycle_type = CycleType.ABNORMAL_CHECK
                else:
                    cycle_type = CycleType.NORMAL_CHECK
                
                self._create_new_cycle(db, cycle_type)
        finally:
            db.close()
    
    def _create_new_cycle(self, db: Session, cycle_type: CycleType, cycle_number: int = 1):
        """創建新循環"""
        # 結束之前的活躍循環
        db.query(CheckCycle).filter(CheckCycle.is_active == True).update({
            "is_active": False,
            "ended_at": datetime.utcnow()
        })
        
        # 獲取區域統計
        zone_manager = ZoneManager(db)
        zone_stats = zone_manager.get_zone_stats()
        
        if cycle_type == CycleType.ABNORMAL_CHECK:
            total_domains = zone_stats.get("ABNORMAL", 0) + zone_stats.get("PENDING", 0)
        else:
            total_domains = zone_stats.get("NORMAL", 0)
        
        # 創建新循環
        cycle = CheckCycle(
            cycle_type=cycle_type,
            cycle_number=cycle_number,
            iteration=1,
            max_iterations=self.max_iterations if cycle_type == CycleType.ABNORMAL_CHECK else 0,
            started_at=datetime.utcnow(),
            is_active=True,
            total_domains=total_domains
        )
        db.add(cycle)
        db.commit()
        db.refresh(cycle)
        
        self.current_cycle_id = cycle.cycle_id
        
        # 記錄日誌
        zone_manager.log_system_event(
            "CYCLE_START",
            f"開始新循環: {cycle_type.value} (第 {cycle_number} 輪)",
            {"cycle_id": cycle.cycle_id, "total_domains": total_domains}
        )
        
        cycle_name = "異常區檢測" if cycle_type == CycleType.ABNORMAL_CHECK else "正常區檢測"
        print(f"\n🔄 開始新循環: {cycle_name} (第 {cycle_number} 輪)")
        print(f"   待檢測域名: {total_domains} 個")
        
        return cycle
    
    async def _switch_to_abnormal_check(self):
        """切換到異常區檢測（第一循環）"""
        print(f"\n{'='*60}")
        print(f"🌙 AM {self.abnormal_check_hour}:00 - 切換到異常區檢測")
        print(f"{'='*60}")
        
        db = self.db_session_factory()
        try:
            # 獲取當前循環編號
            last_cycle = db.query(CheckCycle).filter(
                CheckCycle.cycle_type == CycleType.ABNORMAL_CHECK
            ).order_by(CheckCycle.cycle_number.desc()).first()
            
            cycle_number = (last_cycle.cycle_number + 1) if last_cycle else 1
            self._create_new_cycle(db, CycleType.ABNORMAL_CHECK, cycle_number)
            
            # 立即執行一次檢測
            await self._scheduled_check()
        finally:
            db.close()
    
    async def _switch_to_normal_check(self):
        """切換到正常區檢測（第二循環）"""
        print(f"\n{'='*60}")
        print(f"☀️ AM {self.normal_check_hour}:00 - 切換到正常區檢測")
        print(f"{'='*60}")
        
        db = self.db_session_factory()
        try:
            # 獲取當前循環編號
            last_cycle = db.query(CheckCycle).filter(
                CheckCycle.cycle_type == CycleType.NORMAL_CHECK
            ).order_by(CheckCycle.cycle_number.desc()).first()
            
            cycle_number = (last_cycle.cycle_number + 1) if last_cycle else 1
            self._create_new_cycle(db, CycleType.NORMAL_CHECK, cycle_number)
            
            # 立即執行一次檢測
            await self._scheduled_check()
        finally:
            db.close()
    
    async def _scheduled_check(self):
        """執行排程檢測"""
        if not self.current_cycle_id:
            print("⚠️ 沒有活躍的循環，跳過檢測")
            return
        
        if not self.check_callback:
            print("⚠️ 沒有設置檢測回調函數")
            return
        
        db = self.db_session_factory()
        try:
            cycle = db.query(CheckCycle).filter(
                CheckCycle.cycle_id == self.current_cycle_id
            ).first()
            
            if not cycle or not cycle.is_active:
                print("⚠️ 循環已結束，跳過檢測")
                return
            
            # 檢查是否達到最大檢測次數（僅第一循環）
            if (cycle.cycle_type == CycleType.ABNORMAL_CHECK and 
                cycle.iteration > cycle.max_iterations):
                print(f"📋 第一循環已完成 {cycle.max_iterations} 次檢測，等待切換")
                return
            
            zone_manager = ZoneManager(db)
            
            # 獲取需要檢測的域名
            domains = zone_manager.get_domains_for_check(cycle.cycle_type)
            
            if not domains:
                print(f"📋 沒有需要檢測的域名")
                return
            
            cycle_name = "異常區" if cycle.cycle_type == CycleType.ABNORMAL_CHECK else "正常區"
            print(f"\n{'='*60}")
            print(f"⏰ {cycle_name}檢測 - 第 {cycle.cycle_number} 輪 第 {cycle.iteration} 次")
            print(f"   時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   域名數: {len(domains)}")
            print(f"{'='*60}")
            
            # 執行檢測
            await self.check_callback(
                domains=domains,
                cycle_id=cycle.cycle_id,
                cycle_type=cycle.cycle_type,
                iteration=cycle.iteration
            )
            
            # 更新循環迭代次數
            cycle.iteration += 1
            db.commit()
            
        finally:
            db.close()
    
    async def trigger_check(self) -> Dict:
        """手動觸發檢測"""
        await self._scheduled_check()
        return {"status": "triggered", "cycle": self.get_current_cycle_info()}
    
    def get_current_cycle_info(self) -> Dict:
        """獲取當前循環信息"""
        if not self.current_cycle_id:
            return {"active": False}
        
        db = self.db_session_factory()
        try:
            cycle = db.query(CheckCycle).filter(
                CheckCycle.cycle_id == self.current_cycle_id
            ).first()
            
            if not cycle:
                return {"active": False}
            
            zone_manager = ZoneManager(db)
            zone_stats = zone_manager.get_zone_stats()
            
            return {
                "active": cycle.is_active,
                "cycle_id": cycle.cycle_id,
                "cycle_type": cycle.cycle_type.value,
                "cycle_name": "異常區檢測" if cycle.cycle_type == CycleType.ABNORMAL_CHECK else "正常區檢測",
                "cycle_number": cycle.cycle_number,
                "iteration": cycle.iteration,
                "max_iterations": cycle.max_iterations,
                "started_at": cycle.started_at.isoformat() if cycle.started_at else None,
                "zone_stats": zone_stats,
                "next_switch": self._get_next_switch_time()
            }
        finally:
            db.close()
    
    def _get_next_switch_time(self) -> str:
        """獲取下次切換時間"""
        now = datetime.now()
        current_hour = now.hour
        
        if current_hour < self.abnormal_check_hour:
            next_switch = now.replace(hour=self.abnormal_check_hour, minute=0, second=0)
            switch_to = "異常區檢測"
        elif current_hour < self.normal_check_hour:
            next_switch = now.replace(hour=self.normal_check_hour, minute=0, second=0)
            switch_to = "正常區檢測"
        else:
            next_switch = (now + timedelta(days=1)).replace(
                hour=self.abnormal_check_hour, minute=0, second=0
            )
            switch_to = "異常區檢測"
        
        return f"{next_switch.strftime('%Y-%m-%d %H:%M')} 切換到{switch_to}"
    
    def get_schedule_info(self) -> Dict:
        """獲取排程配置信息"""
        return {
            "abnormal_check_hour": f"AM {self.abnormal_check_hour}:00",
            "normal_check_hour": f"AM {self.normal_check_hour}:00",
            "check_interval_minutes": self.check_interval,
            "max_iterations_per_cycle": self.max_iterations,
            "current_cycle": self.get_current_cycle_info()
        }
