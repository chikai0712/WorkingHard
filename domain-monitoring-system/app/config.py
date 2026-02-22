"""Application configuration using Pydantic Settings"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "postgresql://dms_user:dms_password@postgres:5432/domain_monitoring"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # API Keys
    SECURITYTRAILS_API_KEY: Optional[str] = None
    UPTIMEROBOT_API_KEY: Optional[str] = None
    
    # Slack
    SLACK_WEBHOOK_URL: Optional[str] = None
    
    # Application
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    CHECK_INTERVAL: int = 300  # seconds
    
    # DNS Settings
    DNS_TIMEOUT: int = 3  # seconds
    DNS_MAX_RETRIES: int = 2
    
    # Alert Settings
    ALERT_COOLDOWN: int = 300  # seconds (5 minutes)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

