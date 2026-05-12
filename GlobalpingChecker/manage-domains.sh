#!/bin/bash
# 快捷管理域名狀態
cd "$(dirname "$0")/scripts/management"
bash domain-status-manager.sh "$@"
