#!/bin/bash
# =============================================================
# GlobalpingChecker V4.1 - 部署 + 本機驗證腳本
# 用途：上傳修改後的檔案到 EC2，並執行節點池驗證測試
# 執行：bash deploy_and_test.sh
# =============================================================

set -e

EC2_HOST="54.238.247.106"
EC2_USER="ec2-user"
EC2_KEY="$HOME/.ssh/globalping-checker-key.pem"
EC2_DIR="/home/ec2-user/globalping-v4.1"  # 正式運行目錄
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

SSH_OPTS="-i $EC2_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=15"

echo "=============================================================="
echo " GlobalpingChecker V4.1 - 部署 + 節點池驗證"
echo "=============================================================="
echo " EC2: $EC2_USER@$EC2_HOST"
echo " 本機路徑: $LOCAL_DIR"
echo ""

# --------------------------------------------------------------
# Step 1: 檢查本機檔案
# --------------------------------------------------------------
log "Step 1: 檢查本機檔案..."
for f in app/node_pool.py app/node_validator.py app/main.py test_node_pool.py; do
    if [ ! -f "$LOCAL_DIR/$f" ]; then
        fail "找不到檔案: $LOCAL_DIR/$f"
    fi
    echo "  ✅ $f"
done

# --------------------------------------------------------------
# Step 2: 測試 SSH 連線
# --------------------------------------------------------------
log "Step 2: 測試 SSH 連線到 EC2..."
if ! ssh $SSH_OPTS $EC2_USER@$EC2_HOST 'echo connected' >/dev/null 2>&1; then
    fail "無法連線到 EC2，請確認 VPN/網路正常，以及 Key 路徑: $EC2_KEY"
fi
log "SSH 連線成功"

# --------------------------------------------------------------
# Step 3: 上傳修改後的檔案
# --------------------------------------------------------------
log "Step 3: 上傳檔案到 EC2..."

# 確保目錄存在
ssh $SSH_OPTS $EC2_USER@$EC2_HOST "mkdir -p $EC2_DIR/app"

# 上傳 app 模組檔案
scp $SSH_OPTS \
    "$LOCAL_DIR/app/node_pool.py" \
    "$LOCAL_DIR/app/node_validator.py" \
    "$LOCAL_DIR/app/main.py" \
    $EC2_USER@$EC2_HOST:$EC2_DIR/app/

# 上傳測試腳本
scp $SSH_OPTS \
    "$LOCAL_DIR/test_node_pool.py" \
    $EC2_USER@$EC2_HOST:$EC2_DIR/

log "檔案上傳完成"

EC2_ACTUAL_DIR=$EC2_DIR

# --------------------------------------------------------------
# Step 4: 在 EC2 上安裝依賴 + 重建 node_pool 資料表
# --------------------------------------------------------------
log "Step 4: 複製新檔案進 Docker 容器並重建資料表..."

ssh $SSH_OPTS $EC2_USER@$EC2_HOST "bash -s" <<REMOTE_SETUP
set -e
cd $EC2_ACTUAL_DIR

CONTAINER=\$(docker-compose ps -q web)
echo "[EC2] 容器 ID: \$CONTAINER"

# 複製新版 app 檔案進容器
docker cp app/node_pool.py \$CONTAINER:/app/app/node_pool.py
docker cp app/node_validator.py \$CONTAINER:/app/app/node_validator.py
docker cp app/main.py \$CONTAINER:/app/app/main.py
docker cp test_node_pool.py \$CONTAINER:/app/test_node_pool.py
echo "[EC2] ✅ 檔案已複製進容器"

# 重建 node_pool 資料表
echo "[EC2] 重建 node_pool 資料表（加入 isp_rank 欄位）..."
docker-compose exec -T web python - <<'PYEOF'
import sys
sys.path.insert(0, '.')
try:
    from app.database import Base, engine
    from app.node_pool import NodePool
    Base.metadata.drop_all(bind=engine, tables=[NodePool.__table__])
    Base.metadata.create_all(bind=engine)
    print("[EC2] ✅ node_pool 資料表已重建")
except Exception as e:
    print(f"[EC2] ⚠️  資料表操作: {e}")
PYEOF
REMOTE_SETUP

# --------------------------------------------------------------
# Step 5: 執行驗證測試
# --------------------------------------------------------------
log "Step 5: 執行節點池驗證測試..."
echo ""

ssh $SSH_OPTS $EC2_USER@$EC2_HOST "bash -s" <<REMOTE_TEST
cd $EC2_ACTUAL_DIR
echo "[EC2] 在容器內執行 test_node_pool.py..."
docker-compose exec -T web python test_node_pool.py
REMOTE_TEST

TEST_EXIT=$?

echo ""
# --------------------------------------------------------------
# Step 6: 結果 + 重啟服務
# --------------------------------------------------------------
if [ $TEST_EXIT -eq 0 ]; then
    log "=== 所有測試通過 ==="
    echo ""
    log "Step 6: 重啟 EC2 服務..."
    ssh $SSH_OPTS $EC2_USER@$EC2_HOST "bash -s" <<REMOTE_RESTART
cd $EC2_ACTUAL_DIR
if [ -f docker-compose.yml ]; then
    echo "[EC2] 重啟 Docker 服務..."
    docker-compose restart web 2>/dev/null || docker-compose up -d
    sleep 3
    echo "[EC2] 服務狀態:"
    docker-compose ps
else
    echo "[EC2] ⚠️  找不到 docker-compose.yml，請手動重啟服務"
fi
REMOTE_RESTART
    echo ""
    log "🎉 部署完成！節點池功能已更新並驗證通過。"
else
    warn "=== 部分測試未通過，請檢查上方輸出 ==="
    warn "服務未重啟，請手動處理後重新執行此腳本。"
    exit 1
fi
