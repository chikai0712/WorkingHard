#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TG Commander — 透過 Telegram 傳指令給本機執行

用法：
    python3 tg_commander.py

支援指令（在 TG 傳送）：
    /run <shell指令>     執行任意 shell 指令
    /status              顯示工作區 STATE.md
    /cf                  執行 Cloudflare DNS 統計
    /stock               執行股票分析
    /ps                  顯示目前執行中的 Python 程式
    /help                顯示說明
"""

import subprocess
import logging
import os
import sys
import time

# 強制繞過 Proxy
for _v in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]:
    os.environ.pop(_v, None)

try:
    import telebot
except ImportError:
    print("[ERROR] 缺少 pyTelegramBotAPI，請執行：pip3 install pyTelegramBotAPI")
    sys.exit(1)

# ──────────────────────────────────────────
# 設定
# ──────────────────────────────────────────
BOT_TOKEN     = "8771241397:AAESXT-Cn5EQ6sRBiHar1AKKwiQPKxJ_dJo"
ALLOWED_CHATS = {229891358}   # 白名單 chat_id，只有這些人能控制
WORKSPACE     = "/Users/ckchiu/Desktop/Project"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)


# ──────────────────────────────────────────
# 工具函式
# ──────────────────────────────────────────
def run_cmd(cmd: str, cwd: str = WORKSPACE, timeout: int = 120) -> str:
    """執行 shell 指令，回傳輸出（截斷至 3800 字）"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            cwd=cwd, timeout=timeout
        )
        out = result.stdout + result.stderr
        out = out.strip()
        if not out:
            out = f"[完成，exit code={result.returncode}]"
        if len(out) > 3800:
            out = out[-3800:] + "\n...(已截斷)"
        return out
    except subprocess.TimeoutExpired:
        return f"[TIMEOUT] 指令超過 {timeout}s 尚未完成"
    except Exception as e:
        return f"[ERROR] {e}"


def check_auth(message) -> bool:
    """驗證是否為允許的 chat"""
    if message.chat.id not in ALLOWED_CHATS:
        bot.reply_to(message, "⛔ 未授權")
        logger.warning(f"Unauthorized access from chat_id={message.chat.id}")
        return False
    return True


# ──────────────────────────────────────────
# 指令處理
# ──────────────────────────────────────────
@bot.message_handler(commands=["help", "start"])
def cmd_help(message):
    if not check_auth(message): return
    text = (
        "🤖 *TG Commander — 可用指令*\n\n"
        "`/run <指令>` — 執行任意 shell 指令\n"
        "`/status` — 顯示工作區進度 STATE.md\n"
        "`/cf` — 執行 Cloudflare DNS 統計 (7天)\n"
        "`/stock` — 執行股票分析\n"
        "`/ps` — 顯示執行中 Python 程序\n"
        "`/ls [路徑]` — 列出目錄內容\n"
        "`/help` — 顯示此說明"
    )
    bot.reply_to(message, text, parse_mode="Markdown")


@bot.message_handler(commands=["status"])
def cmd_status(message):
    if not check_auth(message): return
    bot.reply_to(message, "🔍 讀取 STATE.md...")
    out = run_cmd("cat .planning/STATE.md | head -60")
    bot.reply_to(message, f"📋 STATE.md:\n```\n{out}\n```", parse_mode="Markdown")


@bot.message_handler(commands=["cf"])
def cmd_cf(message):
    if not check_auth(message): return
    bot.reply_to(message, "⏳ 執行 Cloudflare DNS 統計（約 2-3 分鐘）...")
    out = run_cmd(
        "source .env && python3 cloudflare_dns_analytics.py --days 7",
        cwd=f"{WORKSPACE}/03-Data-Analytics/Cloudflare-DNS-data",
        timeout=300
    )
    bot.reply_to(message, f"☁️ CF 統計結果:\n```\n{out}\n```", parse_mode="Markdown")


@bot.message_handler(commands=["stock"])
def cmd_stock(message):
    if not check_auth(message): return
    bot.reply_to(message, "⏳ 執行股票分析...")
    out = run_cmd(
        "python3 -m backend.main 2>&1 | tail -50",
        cwd=f"{WORKSPACE}/03-Data-Analytics/Stock_Analize",
        timeout=300
    )
    bot.reply_to(message, f"📈 股票分析:\n```\n{out}\n```", parse_mode="Markdown")


@bot.message_handler(commands=["ps"])
def cmd_ps(message):
    if not check_auth(message): return
    out = run_cmd("pgrep -la python3 2>/dev/null || echo '沒有執行中的 Python 程序'")
    bot.reply_to(message, f"🔧 Python 程序:\n```\n{out}\n```", parse_mode="Markdown")


@bot.message_handler(commands=["ls"])
def cmd_ls(message):
    if not check_auth(message): return
    parts = message.text.split(maxsplit=1)
    path  = parts[1] if len(parts) > 1 else "."
    out   = run_cmd(f"ls -la {path}", cwd=WORKSPACE)
    bot.reply_to(message, f"📁 `{path}`:\n```\n{out}\n```", parse_mode="Markdown")


@bot.message_handler(commands=["run"])
def cmd_run(message):
    if not check_auth(message): return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ 用法：`/run <shell 指令>`", parse_mode="Markdown")
        return
    cmd = parts[1]
    bot.reply_to(message, f"⚙️ 執行：`{cmd}`", parse_mode="Markdown")
    out = run_cmd(cmd)
    bot.reply_to(message, f"```\n{out}\n```", parse_mode="Markdown")


@bot.message_handler(func=lambda m: True)
def fallback(message):
    if not check_auth(message): return
    bot.reply_to(message, "❓ 未知指令，輸入 /help 查看說明")


# ──────────────────────────────────────────
# 主程式
# ──────────────────────────────────────────
if __name__ == "__main__":
    logger.info(f"TG Commander 啟動，監聽 chat_id: {ALLOWED_CHATS}")
    logger.info(f"工作目錄：{WORKSPACE}")
    
    # 發送啟動通知
    try:
        for chat_id in ALLOWED_CHATS:
            bot.send_message(chat_id, "🚀 TG Commander 已啟動！輸入 /help 查看指令。")
    except Exception as e:
        logger.warning(f"啟動通知失敗：{e}")
    
    logger.info("開始 polling...")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
