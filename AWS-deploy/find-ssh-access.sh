#!/bin/bash
# ============================================================
# SSH 診斷腳本 — 自動測試所有密鑰 × 用戶名組合
# 在 Terminal.app / iTerm2（非 Cursor）中執行
# ============================================================

unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
unset ALL_PROXY all_proxy NO_PROXY no_proxy
unset SOCKS_PROXY SOCKS5_PROXY socks_proxy socks5_proxy
unset GIT_HTTP_PROXY GIT_HTTPS_PROXY

EC2_IP="54.238.247.106"
USERS=("ubuntu" "ec2-user" "admin" "centos" "root")
KEYS=(
    "$HOME/.ssh/globalping-checker-key.pem"
    "$HOME/.ssh/my-ec2-key.pem"
    "$HOME/.ssh/pokemon-game-key.pem"
    "$HOME/.ssh/dns-test-key.pem"
)

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  SSH 密鑰 × 用戶名 自動診斷              ║"
echo "║  目標: $EC2_IP                  ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "測試所有組合..."
echo ""

FOUND_KEY=""
FOUND_USER=""

for KEY in "${KEYS[@]}"; do
    if [ ! -f "$KEY" ]; then
        echo "⏭  跳過（不存在）: $KEY"
        continue
    fi
    chmod 400 "$KEY"
    KEY_NAME=$(basename "$KEY")
    
    for USER in "${USERS[@]}"; do
        printf "  測試 %-10s + %-35s ... " "$USER" "$KEY_NAME"
        RESULT=$(ssh -i "$KEY" \
            -o StrictHostKeyChecking=no \
            -o ConnectTimeout=8 \
            -o BatchMode=yes \
            -o PasswordAuthentication=no \
            "$USER@$EC2_IP" 'echo OK' 2>&1)
        
        if echo "$RESULT" | grep -q '^OK$'; then
            echo "✅ 成功！"
            FOUND_KEY="$KEY"
            FOUND_USER="$USER"
            break 2
        elif echo "$RESULT" | grep -q 'Permission denied'; then
            echo "❌ 密鑰不匹配"
        elif echo "$RESULT" | grep -q 'Connection refused'; then
            echo "🚫 Port 22 拒絕連線"
            break 2
        elif echo "$RESULT" | grep -q 'Operation not permitted'; then
            echo "🚫 網路被阻擋（請確認在系統終端執行）"
            break 2
        elif echo "$RESULT" | grep -q 'timed out\|Connection timed out'; then
            echo "⏱  連線逾時"
        else
            echo "❓ $RESULT"
        fi
    done
done

echo ""
if [ -n "$FOUND_KEY" ]; then
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║  ✅ 找到可用的連線組合！                                  ║"
    echo "╠══════════════════════════════════════════════════════════╣"
    printf  "║  用戶: %-50s║\n" "$FOUND_USER"
    printf  "║  密鑰: %-50s║\n" "$(basename $FOUND_KEY)"
    echo "╠══════════════════════════════════════════════════════════╣"
    echo "║  立即連線指令：                                           ║"
    printf  "║  ssh -i %s %s@%s\n" "$(basename $FOUND_KEY)" "$FOUND_USER" "$EC2_IP"
    echo "╠══════════════════════════════════════════════════════════╣"
    echo "║  執行部署（更新部署腳本後執行）：                         ║"
    echo "║  請將以下資訊告訴 Cursor AI：                             ║"
    printf  "║  KEY=%s USER=%s\n" "$(basename $FOUND_KEY)" "$FOUND_USER"
    echo "╚══════════════════════════════════════════════════════════╝"
    
    # 自動更新部署腳本
    DEPLOY_SCRIPT="$HOME/Desktop/Project/AWS-deploy/deploy-v4.1-from-terminal.sh"
    if [ -f "$DEPLOY_SCRIPT" ]; then
        sed -i '' "s|KEY=\".*globalping-checker-key.*\"|KEY=\"$FOUND_KEY\"|" "$DEPLOY_SCRIPT"
        sed -i '' "s|EC2_USER=\"ubuntu\"|EC2_USER=\"$FOUND_USER\"|" "$DEPLOY_SCRIPT"
        sed -i '' "s|EC2_USER=\"ec2-user\"|EC2_USER=\"$FOUND_USER\"|" "$DEPLOY_SCRIPT"
        echo ""
        echo "✅ 部署腳本已自動更新:"
        echo "   $DEPLOY_SCRIPT"
        echo ""
        echo "現在可以執行部署："
        echo "   ~/Desktop/Project/AWS-deploy/deploy-v4.1-from-terminal.sh"
    fi
else
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║  ❌ 所有組合都失敗了                                      ║"
    echo "╠══════════════════════════════════════════════════════════╣"
    echo "║  可能原因：                                               ║"
    echo "║  1. EC2 密鑰已更換 → 需要從 AWS Console 下載新密鑰        ║"
    echo "║  2. 安全組封鎖 port 22 → 在 AWS Console 開放             ║"
    echo "║  3. 使用 EC2 Instance Connect 重設密鑰                   ║"
    echo "╠══════════════════════════════════════════════════════════╣"
    echo "║  替代方案 — EC2 Instance Connect（無需密鑰）：            ║"
    echo "║  AWS Console → EC2 → 選實例 → Connect → EC2 Instance    ║"
    echo "║  Connect → Connect                                       ║"
    echo "╚══════════════════════════════════════════════════════════╝"
fi
echo ""
