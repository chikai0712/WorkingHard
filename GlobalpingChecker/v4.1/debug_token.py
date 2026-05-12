#!/usr/bin/env python3
"""
调试脚本 - 检查 token 和 API 连接
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.config import get_settings

settings = get_settings()

print("🔍 配置检查:")
print(f"   API URL: {settings.globalping_api_url}")
print(f"   Token: {settings.globalping_token}")
print(f"   Token 长度: {len(settings.globalping_token) if settings.globalping_token else 0}")
print(f"   Target Countries: {settings.target_country_list}")
print()

if not settings.globalping_token:
    print("❌ Token 为空！")
    sys.exit(1)

print("✅ Token 已加载")
