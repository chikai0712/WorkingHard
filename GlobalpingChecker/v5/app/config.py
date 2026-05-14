"""
GlobalpingChecker V5 - Configuration

變更自 V4.1：
- 新增多國家動態開關（支援 MY / PH / SG）
- 新增 Telegram 告警設定
- 新增節點池快取 TTL 設定
- 新增 API 額度警戒線設定
"""
from functools import lru_cache
from typing import ClassVar
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Database ─────────────────────────────────────────────
    database_url: str = "sqlite:///./data/globalping_v5.db"

    # ── Globalping API ────────────────────────────────────────
    globalping_api_url: str = "https://api.globalping.io/v1"
    globalping_token: str = ""

    # ── 目標國家開關 ──────────────────────────────────────────
    enable_indonesia: bool = True
    enable_vietnam: bool = False
    enable_thailand: bool = False
    enable_malaysia: bool = False
    enable_philippines: bool = False
    enable_singapore: bool = False

    COUNTRY_MAP: ClassVar[dict] = {
        "indonesia":   {"code": "ID", "name": "Indonesia"},
        "vietnam":     {"code": "VN", "name": "Vietnam"},
        "thailand":    {"code": "TH", "name": "Thailand"},
        "malaysia":    {"code": "MY", "name": "Malaysia"},
        "philippines": {"code": "PH", "name": "Philippines"},
        "singapore":   {"code": "SG", "name": "Singapore"},
    }

    @property
    def target_country_list(self) -> list:
        mapping = [
            (self.enable_indonesia,   "indonesia"),
            (self.enable_vietnam,     "vietnam"),
            (self.enable_thailand,    "thailand"),
            (self.enable_malaysia,    "malaysia"),
            (self.enable_philippines, "philippines"),
            (self.enable_singapore,   "singapore"),
        ]
        codes = [self.COUNTRY_MAP[k]["code"] for flag, k in mapping if flag]
        return codes if codes else ["ID"]

    @property
    def target_country_name_list(self) -> list:
        mapping = [
            (self.enable_indonesia,   "indonesia"),
            (self.enable_vietnam,     "vietnam"),
            (self.enable_thailand,    "thailand"),
            (self.enable_malaysia,    "malaysia"),
            (self.enable_philippines, "philippines"),
            (self.enable_singapore,   "singapore"),
        ]
        names = [self.COUNTRY_MAP[k]["name"] for flag, k in mapping if flag]
        return names if names else ["Indonesia"]

    # ── Scheduler ────────────────────────────────────────────
    check_interval_minutes: int = 90
    abnormal_check_hour: int = 1      # 凌晨 1:00 GMT+8
    normal_check_hour: int = 9        # 早上 9:00 GMT+8
    max_iterations: int = 10
    normal_zone_reset_hour: int = 0   # AM 00:01 正常區全量重置

    # ── Domains / Blocked IPs ────────────────────────────────
    domains_file: str = "domains.txt"
    blocked_ips_file: str = "blocked_ips.txt"

    # ── 節點池設定（V5 新增）─────────────────────────────────
    node_pool_ttl_hours: int = 24       # 節點池快取有效時間（小時）
    node_pool_refresh_hour: int = 3     # 每天幾點自動刷新節點池
    nodes_per_country: int = 5          # 每個國家取幾個節點

    # ── API 額度警戒線（V5 新增）────────────────────────────
    api_quota_warning_threshold: int = 50   # 剩餘額度低於此值時告警
    api_quota_wait_on_error: int = 3600     # API Error 後等待秒數

    # ── Telegram 告警（V5 新增）────────────────────────────
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_notify_on_zone_change: bool = True
    telegram_notify_on_api_error: bool = True
    telegram_notify_on_cycle_complete: bool = False

    # ── Web Server ───────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
