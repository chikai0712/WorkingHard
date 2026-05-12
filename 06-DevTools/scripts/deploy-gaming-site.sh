#!/bin/bash
# 快速部署博弈網站腳本（使用 dns-test-key）

cd /Users/ckchiu/Desktop/Project

# 自動選擇密鑰 1 (dns-test-key.pem) 並確認部署
echo -e "1\ny" | bash scripts/deploy-website.sh 2
