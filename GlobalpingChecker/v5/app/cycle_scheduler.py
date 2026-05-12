"""
GlobalpingChecker V5 - Cycle Scheduler
簡化版：每日 AM 00:01 全量重置所有域名並觸發一次完整檢測。
移除了 ABNORMAL/NORMAL 分區排程，改為單一全量模式。
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

from .models import CheckCycle, CycleType, DomainZone
from .zone_manager import ZoneManager
from .config import get_settings

settings = get_settings()


class CycleScheduler:
    """簡化循環排程器 — 每日 AM 00:01 全量檢測"""

    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.scheduler = AsyncIOScheduler()
        self.current_cycle_id: Optional[int] = None
        self.check_callback = None

        # 設定（由 main.py 啟動時注入）
        self.daily_reset_hour   = 0   # AM 00:01 全量重置並開始檢測
        self.daily_reset_minute = 1
        self.max_iterations     = 1   # 全量模式每天只跑一次

    def set_check_callback(self, callback):
        self.check_callback = callback

    def start(self):
        """啟動排程器：只有一個 cron job — AM 00:01 全量重置 + 檢測"""
        self.scheduler.add_job(
            self._daily_full_check,
            CronTrigger(
                hour=self.daily_reset_hour,
                minute=self.daily_reset_minute,
                timezone=ZoneInfo("Asia/Taipei")
            ),
            id="daily_full_check",
            name="每日全量重置並檢測 AM 00:01",
            replace_existing=True
        )
        self.scheduler.start()

        # 啟動時初始化一個循環（供手動觸發使用）
        self._initialize_cycle()

        print(f"⏰ V5 排程器已啟動")
        print(f"   - AM {self.daily_reset_hour:02d}:{self.daily_reset_minute:02d} 每日全量重置並檢測")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("⏰ 排程器已停止")

    def _initialize_cycle(self):
        """啟動時建立或恢復一個 cycle，供手動觸發使用"""
        db = self.db_session_factory()
        try:
            active = (
                db.query(CheckCycle)
                .filter(CheckCycle.is_active == True)
                .order_by(CheckCycle.started_at.desc())
                .first()
            )
            if active:
                self.current_cycle_id = active.cycle_id
                print(f"📋 恢復現有循環 #{active.cycle_id} (第 {active.cycle_number} 輪)")
            else:
                cycle = self._create_cycle(db)
                print(f"📋 建立新循環 #{cycle.cycle_id}")
        finally:
            db.close()

    def _create_cycle(self, db: Session) -> CheckCycle:
        """建立新的全量循環"""
        # 結束舊循環
        db.query(CheckCycle).filter(CheckCycle.is_active == True).update(
            {"is_active": False, "ended_at": datetime.utcnow()}
        )

        zm = ZoneManager(db)
        zone_stats  = zm.get_zone_stats()
        total = sum(zone_stats.values())

        last = (
            db.query(CheckCycle)
            .order_by(CheckCycle.cycle_number.desc())
            .first()
        )
        cycle_number = (last.cycle_number + 1) if last else 1

        cycle = CheckCycle(
            cycle_type     = CycleType.ABNORMAL_CHECK,  # 沿用原有 enum，代表全量
            cycle_number   = cycle_number,
            iteration      = 1,
            max_iterations = self.max_iterations,
            started_at     = datetime.utcnow(),
            is_active      = True,
            total_domains  = total,
        )
        db.add(cycle)
        db.commit()
        db.refresh(cycle)

        self.current_cycle_id = cycle.cycle_id

        zm.log_system_event(
            "CYCLE_START",
            f"開始新全量循環 (第 {cycle_number} 輪)，共 {total} 個域名",
            {"cycle_id": cycle.cycle_id, "total_domains": total}
        )
        print(f"\n🔄 全量循環 #{cycle.cycle_id} 開始（第 {cycle_number} 輪，{total} 個域名）")
        return cycle

    async def _daily_full_check(self):
        """AM 00:01 — 重置所有域名為 PENDING，確認額度後執行全量檢測"""
        print(f"\n{'='*60}")
        print(f"🔄 AM 00:01 — 每日全量重置並檢測")
        print(f"{'='*60}")

        db = self.db_session_factory()
        try:
            zm    = ZoneManager(db)
            count = zm.reset_normal_to_pending()
            zm.log_system_event(
                "DAILY_RESET",
                f"每日全量重置：{count} 個正常區域名移回 PENDING",
                {"reset_count": count}
            )
            print(f"   ✅ {count} 個正常區域名已移回 PENDING")
            self._create_cycle(db)
        finally:
            db.close()

        # 額度確認在 checker.run_cycle_check 內部進行
        await self._run_check()

    async def _run_check(self):
        """取得所有待檢測域名並執行（額度確認在 checker 內部）"""
        if not self.check_callback:
            print("⚠️ 未設置檢測回調")
            return

        db = self.db_session_factory()
        try:
            cycle = db.query(CheckCycle).filter(
                CheckCycle.cycle_id == self.current_cycle_id
            ).first()
            if not cycle or not cycle.is_active:
                print("⚠️ 無活躍循環，跳過")
                return

            zm      = ZoneManager(db)
            # 全量：撈 PENDING + ABNORMAL（正常區已重置回 PENDING）
            domains = (
                zm.get_domain_names_by_zone(DomainZone.PENDING) +
                zm.get_domain_names_by_zone(DomainZone.ABNORMAL)
            )

            if not domains:
                print("📋 無待檢測域名")
                return

            print(f"⏰ 全量檢測啟動 — {len(domains)} 個域名")
            print(f"   時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        finally:
            db.close()

        # 執行全量檢測（checker 內部會先確認 API 額度）
        await self.check_callback(
            domains    = domains,
            cycle_id   = self.current_cycle_id,
            cycle_type = CycleType.ABNORMAL_CHECK,
            iteration  = 1,
        )

        # 全量跑完後，持續輪詢正常區
        await self._poll_normal_zone(start_iteration=2)

    async def _poll_normal_zone(self, start_iteration: int = 2):
        """
        全量檢測完成後，持續輪詢正常區：
        - 每輪結束後立即查詢 API 額度
        - 有足夠額度 → 立即繼續下一輪
        - 額度不足   → 等到下次 AM 00:01
        - 距下次 AM 00:01 不足 30 分鐘 → 停止輪詢
        """
        import app.checker as checker_mod
        import httpx
        iteration = start_iteration
        tz_taipei = ZoneInfo("Asia/Taipei")

        while True:
            # ── 1. 距下次 AM 00:01 還有多久 ──────────────────────────
            now = datetime.now(tz=tz_taipei)
            nxt = now.replace(hour=self.daily_reset_hour,
                              minute=self.daily_reset_minute,
                              second=0, microsecond=0)
            if nxt <= now:
                nxt += timedelta(days=1)
            seconds_to_reset = (nxt - now).total_seconds()

            if seconds_to_reset < 1800:
                print(f"\n⏳ 距下次全量重置不足 30 分鐘，停止輪詢")
                break

            # ── 2. 檢查停止旗標 ───────────────────────────────────────
            if checker_mod._stop_flag:
                print("⏹️  正常區輪詢已暫停")
                checker_mod._stop_flag = False
                break

            # ── 3. 取得待輪詢域名（NORMAL + ABNORMAL）────────────────
            db = self.db_session_factory()
            try:
                zm = ZoneManager(db)
                normal_domains   = zm.get_domain_names_by_zone(DomainZone.NORMAL)
                abnormal_domains = zm.get_domain_names_by_zone(DomainZone.ABNORMAL)
            finally:
                db.close()

            poll_domains = normal_domains + abnormal_domains
            if not poll_domains:
                print("\n✅ 無域名需要輪詢，停止")
                break

            # ── 4. 查詢 API 額度，計算本輪能跑幾個 ───────────────────
            from .checker import GlobalpingChecker
            checker_inst = GlobalpingChecker()
            remaining = 0
            try:
                async with httpx.AsyncClient() as client:
                    limits = await checker_inst.check_api_limits(client)
                if limits:
                    remaining = (
                        limits.get('rateLimit', {})
                        .get('measurements', {}).get('create', {}).get('remaining', 0)
                    )
            except Exception as e:
                print(f"⚠️  額度查詢失敗: {e}，跳過本輪")
                await asyncio.sleep(60)
                continue

            required_per_domain = len(checker_inst.target_countries) * 2
            max_domains = remaining // required_per_domain if required_per_domain > 0 else 0

            print(f"\n📊 輪詢額度檢查: 剩餘 {remaining} / 每域名需 {required_per_domain} / 可跑 {max_domains} 個")

            if max_domains == 0:
                # 額度耗盡，計算距下一個整點還有多久（Globalping 每小時整點重置）
                now_taipei = datetime.now(tz=tz_taipei)
                minutes_to_next_hour = 60 - now_taipei.minute
                seconds_to_next_hour = minutes_to_next_hour * 60 - now_taipei.second
                print(f"⏳ API 額度耗盡（剩餘 {remaining}），等待 {minutes_to_next_hour} 分鐘至下一個整點恢復...")

                # 等待期間每秒檢查停止旗標
                for _ in range(seconds_to_next_hour + 30):  # 多等 30 秒確保額度已刷新
                    if checker_mod._stop_flag:
                        print("⏹️  等待額度恢復期間收到暫停指令")
                        checker_mod._stop_flag = False
                        return
                    await asyncio.sleep(1)
                print("🔄 額度應已恢復，重新檢查...")
                continue  # 回到 while True 頂部重新查詢額度

            # 若可跑數量少於全部域名，優先跑異常區
            if max_domains < len(poll_domains):
                domains_this_round = (abnormal_domains + normal_domains)[:max_domains]
                print(f"⚠️  額度有限，本輪優先跑異常區，共 {len(domains_this_round)} 個")
            else:
                domains_this_round = poll_domains

            # ── 5. 執行本輪檢測 ───────────────────────────────────────
            print(f"\n🔄 持續輪詢第 {iteration-1} 輪（{len(domains_this_round)} 個域名）")
            await self.check_callback(
                domains    = domains_this_round,
                cycle_id   = self.current_cycle_id,
                cycle_type = CycleType.ABNORMAL_CHECK,
                iteration  = iteration,
            )
            iteration += 1
            # 每輪結束立即進入下一輪（頂部重新檢查額度和時間）

    async def trigger_check(self) -> Dict:
        """手動觸發：不重置，直接撈現有 PENDING+ABNORMAL 檢測，完成後輪詢正常區"""
        await self._run_check()
        return {"status": "triggered", "cycle": self.get_current_cycle_info()}

    def get_current_cycle_info(self) -> Dict:
        if not self.current_cycle_id:
            return {"active": False}
        db = self.db_session_factory()
        try:
            cycle = db.query(CheckCycle).filter(
                CheckCycle.cycle_id == self.current_cycle_id
            ).first()
            if not cycle:
                return {"active": False}

            zm         = ZoneManager(db)
            zone_stats = zm.get_zone_stats()

            now = datetime.now(tz=ZoneInfo("Asia/Taipei"))
            nxt = now.replace(hour=self.daily_reset_hour,
                              minute=self.daily_reset_minute,
                              second=0, microsecond=0)
            if nxt <= now:
                nxt += timedelta(days=1)

            return {
                "active":        cycle.is_active,
                "cycle_id":      cycle.cycle_id,
                "cycle_type":    cycle.cycle_type.value,
                "cycle_name":    "全量檢測",
                "cycle_number":  cycle.cycle_number,
                "iteration":     cycle.iteration,
                "max_iterations": cycle.max_iterations,
                "started_at":    cycle.started_at.isoformat() if cycle.started_at else None,
                "zone_stats":    zone_stats,
                "next_switch":   nxt.strftime('%Y-%m-%d %H:%M') + " 下次全量檢測",
            }
        finally:
            db.close()

    def get_schedule_info(self) -> Dict:
        return {
            "mode":                   "daily_full_check",
            "daily_reset_time":       f"AM {self.daily_reset_hour:02d}:{self.daily_reset_minute:02d}",
            "description":            "每日 AM 00:01 重置所有域名並全量重新檢測",
            "current_cycle":          self.get_current_cycle_info(),
        }
