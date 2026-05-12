"""
GlobalpingChecker V4 - Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://globalping:password@localhost:5432/globalping_db"
    
    # Globalping API
    globalping_token: str = ""
    globalping_api_url: str = "https://api.globalping.io/v1"
    
    # Scheduler
    check_interval_minutes: int = 90
    domains_file: str = "domains.txt"
    
    # Web Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # AWS
    aws_region: str = "ap-southeast-1"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 忽略額外的環境變數


@lru_cache()
def get_settings() -> Settings:
    return Settings()
