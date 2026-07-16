"""全域常數與路徑設定。所有模組從這裡 import，不在各檔案硬編碼。"""
import os
from pathlib import Path

# 載入 .env（不強制依賴 python-dotenv，手動 parse 即可）
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# macOS Docker Desktop 用自己的 socket，不走 /var/run/docker.sock。
# 設定 DOCKER_HOST 讓所有 subprocess 呼叫 docker CLI 時自動套用，
# 不依賴 docker context（子 process 不一定繼承 context 設定）。
_docker_sock = Path.home() / ".docker" / "run" / "docker.sock"
if _docker_sock.exists() and not os.environ.get("DOCKER_HOST"):
    os.environ["DOCKER_HOST"] = f"unix://{_docker_sock}"

BASE_DIR     = Path(__file__).parent.parent
DOCKER_DIR   = BASE_DIR / "lab" / "docker"
PRESETS_DIR  = BASE_DIR / "presets"
REPORTS_DIR  = BASE_DIR / "reports"
TEMPLATES_DIR= BASE_DIR / "templates"

REPORT_SCRIPT = BASE_DIR / "report-generator" / "generate_report.py"
VENV_PYTHON   = BASE_DIR / "report-generator" / ".venv" / "bin" / "python3"

REPORTS_DIR.mkdir(exist_ok=True)

DD_URL   = "http://localhost:8001"
DD_TOKEN = os.environ.get("DD_TOKEN", "")

KAFKA_URL = "http://localhost:8082"

ZAP_API = "http://localhost:8090"
ZAP_KEY = os.environ.get("ZAP_KEY", "redsaas")

NUCLEI_TEMPLATES_DIR = BASE_DIR / "lab" / "nuclei-templates"
