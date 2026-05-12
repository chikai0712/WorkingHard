#!/bin/bash
# TG Commander 啟動腳本
# 用法：bash start_tg_commander.sh

cd /Users/ckchiu/Desktop/Project

# 建立 venv（如果不存在）
if [ ! -d ".venv" ]; then
    echo "[INFO] 建立虛擬環境..."
    python3 -m venv .venv
fi

# 啟動 venv
source .venv/bin/activate

# 安裝依賴
echo "[INFO] 檢查依賴..."
pip install pyTelegramBotAPI --quiet

# 啟動 TG Commander
echo "[INFO] 啟動 TG Commander..."
python3 tg_commander.py
