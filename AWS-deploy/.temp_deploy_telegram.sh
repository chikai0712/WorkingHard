#!/bin/bash

# 禁用代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY
unset socks_proxy SOCKS_PROXY socks5_proxy SOCKS5_PROXY
unset GIT_HTTP_PROXY GIT_HTTPS_PROXY

cd "$(dirname "$0")"

echo "========================================"
echo "部署 Telegram 通知到 EC2"
echo "========================================"
echo ""

./deploy-telegram-to-ec2.sh

echo ""
echo "按 Enter 關閉此視窗..."
read
