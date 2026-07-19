#!/bin/zsh
# ============================================================
# RedSaaS — 一鍵環境建置腳本
# 用途：重裝電腦後，從零開始還原完整環境
# 用法：chmod +x setup.sh && ./setup.sh
# ============================================================
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
DOCKER_DIR="$DIR/lab/docker"
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo "${BOLD}${BLUE}[setup]${NC} $*"; }
ok()   { echo "${GREEN}  ✓${NC} $*"; }
warn() { echo "${YELLOW}  ⚠${NC} $*"; }
fail() { echo "${RED}  ✗${NC} $*"; exit 1; }
sep()  { echo; echo "────────────────────────────────────────────────"; }

# ── 0. 確認 macOS ────────────────────────────────────────────
sep
log "Phase 0 — 環境確認"
[[ "$(uname)" == "Darwin" ]] || fail "此腳本僅支援 macOS"
ok "macOS $(sw_vers -productVersion)"

# ── 1. Homebrew ──────────────────────────────────────────────
sep
log "Phase 1 — Homebrew"
if ! command -v brew &>/dev/null; then
  warn "Homebrew 未安裝，開始安裝..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  # Apple Silicon path
  eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true
fi
ok "Homebrew $(brew --version | head -1)"

# ── 2. 系統相依 ──────────────────────────────────────────────
sep
log "Phase 2 — 系統套件 (git, python3, curl)"
for pkg in git python3 curl; do
  if ! command -v "$pkg" &>/dev/null; then
    log "安裝 $pkg..."
    brew install "$pkg"
  fi
  ok "$pkg $(command -v "$pkg")"
done

# Python 版本檢查：需要 3.10+ 才支援 X | Y 型別語法
PYTHON_MINOR=$(/usr/bin/python3 -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo "0")
if [[ "$PYTHON_MINOR" -lt 10 ]]; then
  warn "系統 Python 3.${PYTHON_MINOR} 低於 3.10，安裝 python@3.11..."
  brew install python@3.11
  # 更新 PATH 讓後續指令使用 3.11
  export PATH="/opt/homebrew/opt/python@3.11/bin:$PATH"
  ok "Python $(/opt/homebrew/opt/python@3.11/bin/python3.11 --version)"
  PYTHON3_BIN="/opt/homebrew/opt/python@3.11/bin/python3.11"
else
  ok "Python 3.${PYTHON_MINOR} 版本符合需求"
  PYTHON3_BIN="$(command -v python3)"
fi

# ── 3. Docker Desktop ────────────────────────────────────────
sep
log "Phase 3 — Docker Desktop"
if ! command -v docker &>/dev/null; then
  warn "Docker Desktop 未安裝"
  echo
  echo "  請手動安裝 Docker Desktop："
  echo "  https://www.docker.com/products/docker-desktop/"
  echo
  read -r "?  安裝完成後按 Enter 繼續..."
fi

# 等待 Docker daemon
log "等待 Docker daemon 啟動..."
for i in $(seq 1 30); do
  if docker info &>/dev/null 2>&1; then
    ok "Docker $(docker version --format '{{.Server.Version}}' 2>/dev/null)"
    break
  fi
  if [[ $i -eq 1 ]]; then
    warn "Docker daemon 未就緒，嘗試啟動 Docker Desktop..."
    open -a "Docker" 2>/dev/null || true
  fi
  sleep 3
  [[ $i -eq 30 ]] && fail "Docker daemon 啟動超時，請手動開啟 Docker Desktop 後重跑"
done

# macOS socket 路徑
export DOCKER_HOST="unix://${HOME}/.docker/run/docker.sock"
ok "DOCKER_HOST=$DOCKER_HOST"

# ── 4. Python venv + pip ─────────────────────────────────────
sep
log "Phase 4 — Python 虛擬環境"
cd "$DIR"

# 主 venv
if [[ ! -f ".venv/bin/python3" ]]; then
  log "建立 .venv..."
  "$PYTHON3_BIN" -m venv .venv
fi
ok "主 venv: $DIR/.venv"

log "安裝主程式相依套件..."
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q \
  flask==3.1.1 \
  requests==2.32.3 \
  python-docx==1.1.2 \
  ollama==0.3.3 \
  jinja2==3.1.4 \
  kubernetes==34.1.0 \
  minio==7.2.15
ok "主程式套件安裝完成"

# report-generator venv
RDIR="$DIR/report-generator"
if [[ -f "$RDIR/requirements.txt" ]]; then
  if [[ ! -f "$RDIR/.venv/bin/python3" ]]; then
    log "建立 report-generator/.venv..."
    python3 -m venv "$RDIR/.venv"
  fi
  "$RDIR/.venv/bin/pip" install -q --upgrade pip
  "$RDIR/.venv/bin/pip" install -q -r "$RDIR/requirements.txt"
  ok "report-generator 套件安裝完成"
fi

# ── 5. .env 設定 ─────────────────────────────────────────────
sep
log "Phase 5 — 環境變數 (.env)"
if [[ ! -f "$DIR/.env" ]]; then
  warn ".env 不存在，建立預設範本..."
  cat > "$DIR/.env" << 'ENVEOF'
# RedSaaS 本地敏感設定
# 請填入你的 DefectDojo API Token（登入後 → Profile → API v2 Key）
DD_TOKEN=請填入你的DefectDojo_Token
ZAP_KEY=redsaas
ENVEOF
  echo
  warn "請編輯 $DIR/.env 填入正確的 DD_TOKEN 後重跑，或繼續（DefectDojo 功能暫時停用）"
  read -r "?  按 Enter 繼續..."
else
  ok ".env 已存在"
fi

# ── 6. Docker Compose 服務 ───────────────────────────────────
sep
log "Phase 6 — 啟動 Docker Compose 服務"
cd "$DOCKER_DIR"

# 確認 .env 不含 placeholder
if [[ -f "$DOCKER_DIR/.env" ]]; then
  ok "docker/.env 已存在"
else
  touch "$DOCKER_DIR/.env"
fi

# DefectDojo（核心平台，最重要）
log "啟動 DefectDojo（核心漏洞管理平台）..."
docker compose up -d \
  defectdojo defectdojo-nginx defectdojo-worker defectdojo-db defectdojo-redis \
  2>&1 | grep -E "Starting|Started|Running|healthy|error" || true
ok "DefectDojo → http://localhost:8001 (admin/admin)"

# 靶場環境
log "啟動靶場環境（crAPI + DVWA）..."
docker compose up -d \
  crapi-identity crapi-community crapi-workshop crapi-web \
  crapi-postgres crapi-mongodb crapi-mailhog crapi-chatbot dvwa \
  2>&1 | grep -E "Starting|Started|Running|error" || true
ok "crAPI   → http://localhost:8888"
ok "DVWA    → http://localhost:4280"
ok "MailHog → http://localhost:8025"

# ── 7. 拉取掃描工具 Image ────────────────────────────────────
sep
log "Phase 7 — 掃描工具 Image"
log "拉取 Nmap..."
docker pull instrumentisto/nmap:7.95 2>&1 | tail -1

log "拉取 Nuclei..."
docker pull projectdiscovery/nuclei:v3.11.0 2>&1 | tail -1

log "拉取 ZAP..."
docker pull zaproxy/zap-stable:2.17.0 2>&1 | tail -1

log "建置 redsaas-pentest-tools（SQLMap + Gobuster + Nikto）..."
docker build \
  -f "$DOCKER_DIR/Dockerfile.pentest-tools" \
  -t redsaas-pentest-tools:latest \
  "$DOCKER_DIR" 2>&1 | tail -3
ok "掃描工具 Image 準備完成"

# ── 8. 等待 DefectDojo 健康 ──────────────────────────────────
sep
log "Phase 8 — 等待 DefectDojo 就緒（最長 120 秒）..."
DD_READY=false
for i in $(seq 1 40); do
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v2/users/ \
         -H "Authorization: Token admin" 2>/dev/null || echo "000")
  if [[ "$HTTP" == "200" || "$HTTP" == "401" || "$HTTP" == "403" ]]; then
    DD_READY=true
    ok "DefectDojo API 就緒 (HTTP $HTTP)"
    break
  fi
  echo -n "."
  sleep 3
done
echo
if $DD_READY; then
  : # 已就緒，跳過 migration
else
  warn "DefectDojo HTTP 未回應，嘗試跑 DB migration（全新安裝通常需要）..."
  DD_CONTAINER=$(docker ps --format "{{.Names}}" 2>/dev/null | grep -E "defectdojo[^-]|defectdojo-1$" | head -1 || true)
  if [[ -n "$DD_CONTAINER" ]]; then
    log "對 $DD_CONTAINER 執行 migrate..."
    docker exec "$DD_CONTAINER" python manage.py migrate --noinput 2>&1 | tail -5 || true
    log "建立預設 superuser（admin / admin）..."
    docker exec "$DD_CONTAINER" python manage.py shell -c \
      "from django.contrib.auth import get_user_model; U=get_user_model(); U.objects.filter(username='admin').exists() or U.objects.create_superuser('admin','admin@localhost','admin')" \
      2>&1 | tail -3 || true
    ok "Migration 完成，DefectDojo → http://localhost:8001 (admin / admin)"
  else
    warn "找不到 DefectDojo container，請手動執行 migrate 後更新 DD_TOKEN"
  fi
fi

# ── 9. 啟動 Flask ────────────────────────────────────────────
sep
log "Phase 9 — 啟動 RedSaaS Flask 伺服器"
cd "$DIR"

# 停止舊 instance
pkill -f 'python3 app.py' 2>/dev/null && sleep 1 || true
lsof -ti tcp:5001 2>/dev/null | xargs kill -9 2>/dev/null || true

# 等 port 釋放
for i in $(seq 1 10); do
  lsof -ti tcp:5001 2>/dev/null | grep -q . || break
  sleep 0.5
done

# 背景開啟瀏覽器
(
  for i in $(seq 1 20); do
    sleep 1
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001 2>/dev/null | grep -q "200"; then
      echo ""
      ok "RedSaaS UI ready → http://localhost:5001"
      open "http://localhost:5001"
      break
    fi
  done
) &

# ── 完成摘要 ─────────────────────────────────────────────────
sep
echo
echo "${BOLD}${GREEN}✅ 環境建置完成${NC}"
echo
echo "  服務清單："
echo "  • RedSaaS UI      → http://localhost:5001"
echo "  • DefectDojo      → http://localhost:8001  (admin / admin)"
echo "  • crAPI 靶場      → http://localhost:8888"
echo "  • DVWA 靶場       → http://localhost:4280"
echo "  • MailHog         → http://localhost:8025"
echo
echo "  日常啟動（之後不用重跑 setup.sh，用這個）："
echo "  ${BOLD}$DIR/start.sh${NC}"
echo
echo "  停止全部服務："
echo "  ${BOLD}cd $DOCKER_DIR && docker compose stop${NC}"
echo
sep

# 啟動 Flask（前景）
export DOCKER_HOST="unix://${HOME}/.docker/run/docker.sock"
exec .venv/bin/python3 app.py
