#!/bin/bash
# 快捷執行智能分區檢測
cd "$(dirname "$0")/scripts/detection"
bash smart-zone-check.sh ../../data/domains.txt "$@"
