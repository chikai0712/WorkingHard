#!/bin/zsh
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=5001
URL="http://localhost:${PORT}"

echo "🔴 RedSaaS 啟動中..."

# 清理舊 process（等確實釋放 port）
pkill -f 'python3 app.py' 2>/dev/null && echo "  停止舊 instance" || true
for i in $(seq 1 10); do
  lsof -ti tcp:${PORT} 2>/dev/null | xargs kill -9 2>/dev/null || true
  lsof -ti tcp:${PORT} 2>/dev/null | grep -q . || break
  sleep 0.5
done

# Docker Desktop socket
export DOCKER_HOST="unix://${HOME}/.docker/run/docker.sock"

# 啟動 Flask（前景，Ctrl+C 可停止）
cd "$DIR"

# 等 Flask ready 再開瀏覽器（背景輪詢）
(
  for i in $(seq 1 20); do
    sleep 0.5
    if curl -s -o /dev/null -w "%{http_code}" "${URL}" 2>/dev/null | grep -q "200"; then
      echo "  ✓ UI ready → ${URL}"
      open "${URL}"
      break
    fi
  done
) &

.venv/bin/python3 app.py
