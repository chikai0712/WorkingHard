"""
GlobalpingChecker V4.1 - Configuration
"""
from functools import lru_cache
from typing import ClassVar
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./data/globalping_results.db"
    
    # Globalping API
    globalping_api_url: str = "https://api.globalping.io/v1"
    globalping_token: str = ""
    
    # Target Countries Switches (國家開關)
    enable_indonesia: bool = True
    enable_vietnam: bool = False
    enable_thailand: bool = False
    
    # 國家映射 (使用 ClassVar 避免 Pydantic 錯誤)
    COUNTRY_MAP: ClassVar[dict] = {
        "indonesia": {"code": "ID", "name": "Indonesia"},
        "vietnam": {"code": "VN", "name": "Vietnam"},
        "thailand": {"code": "TH", "name": "Thailand"}
    }
    
    @property
    def target_country_list(self) -> list:
        """根據開關返回啟用的國家代碼列表"""
        countries = []
        if self.enable_indonesia:
            countries.append(self.COUNTRY_MAP["indonesia"]["code"])
        if self.enable_vietnam:
            countries.append(self.COUNTRY_MAP["vietnam"]["code"])
        if self.enable_thailand:
            countries.append(self.COUNTRY_MAP["thailand"]["code"])
        
        # 如果沒有啟用任何國家，默認啟用印尼
        if not countries:
            countries.append("ID")
        
        return countries
    
    @property
    def target_country_name_list(self) -> list:
        """根據開關返回啟用的國家名稱列表"""
        names = []
        if self.enable_indonesia:
            names.append(self.COUNTRY_MAP["indonesia"]["name"])
        if self.enable_vietnam:
            names.append(self.COUNTRY_MAP["vietnam"]["name"])
        if self.enable_thailand:
            names.append(self.COUNTRY_MAP["thailand"]["name"])
        
        # 如果沒有啟用任何國家，默認啟用印尼
        if not names:
            names.append("Indonesia")
        
        return names
    
    # Scheduler
    check_interval_minutes: int = 90
    abnormal_check_hour: int = 1      # AM 1:00
    normal_check_hour: int = 9        # AM 9:00
    max_iterations: int = 10          # 第一循環最大檢測次數
    
    # Domains
    domains_file: str = "domains.txt"
    
    # Blocked IPs 清單檔案
    blocked_ips_file: str = "blocked_ips.txt"
    
    # Web Server
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
