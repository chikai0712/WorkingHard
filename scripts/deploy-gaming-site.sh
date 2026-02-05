#!/bin/bash
# 快速部署博弈網站腳本

cd /Users/ckchiu/Desktop/Project

# 自動選擇密鑰 2 並確認部署
echo -e "2\ny" | bash scripts/deploy-website.sh 2
