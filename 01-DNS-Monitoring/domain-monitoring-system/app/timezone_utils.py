"""Timezone utilities for converting UTC to local time"""
from datetime import datetime
from zoneinfo import ZoneInfo
from app.config import settings


def get_local_timezone():
    """獲取本地時區"""
    return ZoneInfo(settings.TIMEZONE)


def utc_now():
    """獲取當前 UTC 時間"""
    return datetime.now(ZoneInfo("UTC"))


def local_now():
    """獲取當前本地時間"""
    return datetime.now(get_local_timezone())


def utc_to_local(dt: datetime) -> datetime:
    """
    將 UTC 時間轉換為本地時間
    
    Args:
        dt: UTC datetime object (naive or aware)
        
    Returns:
        本地時區的 datetime object
    """
    if dt is None:
        return None
    
    # 如果是 naive datetime，假設它是 UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    
    # 轉換為本地時區
    return dt.astimezone(get_local_timezone())


def local_to_utc(dt: datetime) -> datetime:
    """
    將本地時間轉換為 UTC
    
    Args:
        dt: 本地 datetime object (naive or aware)
        
    Returns:
        UTC 時區的 datetime object
    """
    if dt is None:
        return None
    
    # 如果是 naive datetime，假設它是本地時間
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=get_local_timezone())
    
    # 轉換為 UTC
    return dt.astimezone(ZoneInfo("UTC"))


def format_local_time(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化為本地時間字符串
    
    Args:
        dt: datetime object
        format_str: 格式字符串
        
    Returns:
        格式化的時間字符串
    """
    if dt is None:
        return ""
    
    local_dt = utc_to_local(dt)
    return local_dt.strftime(format_str)

