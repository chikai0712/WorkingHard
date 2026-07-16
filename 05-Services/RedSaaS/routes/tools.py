"""routes/tools.py — 工具中心、套組清單、工具啟停。"""
from __future__ import annotations
import subprocess

from flask import Blueprint, jsonify

from core.config import DOCKER_DIR

bp = Blueprint("tools", __name__)

TOOL_PRESETS = [
    {"id": "recon",    "name": "🔴 快速偵察",   "desc": "外部暴露面掃描，適合授權測試第一階段",
     "color": "#ef4444", "bg": "rgba(239,68,68,.08)", "border": "rgba(239,68,68,.3)",
     "tools": ["nmap","nuclei","defectdojo","report"], "yaml": "presets/quick-recon.yaml",
     "phases": ["偵察","漏洞發現","歸檔","報告"]},
    {"id": "web",      "name": "🟠 Web 滲透",    "desc": "OWASP Top 10 全套，適合 Web 應用滲透測試",
     "color": "#f97316", "bg": "rgba(249,115,22,.08)", "border": "rgba(249,115,22,.3)",
     "tools": ["nmap","nuclei","zap","sqlmap","gobuster","nikto","defectdojo","report"],
     "yaml": "presets/web-pentest.yaml",
     "phases": ["埠掃描","漏洞模板","DAST","注入","路徑枚舉","伺服器弱點","歸檔","報告"]},
    {"id": "apt",      "name": "🟣 紅隊 APT",    "desc": "完整攻擊鏈模擬，偵察→突破→橫移→控制",
     "color": "#a855f7", "bg": "rgba(168,85,247,.08)", "border": "rgba(168,85,247,.3)",
     "tools": ["nmap","nuclei","sqlmap","sliver","metasploit","bloodhound","defectdojo","report"],
     "yaml": "presets/apt-simulation.yaml",
     "phases": ["資產盤點","漏洞發現","漏洞利用","C2植入","後滲透","AD路徑","歸檔","報告"]},
    {"id": "redblue",  "name": "🔵 紅藍對抗",   "desc": "紅隊攻擊全程寫入 Kafka，藍隊即時監控攔截",
     "color": "#3b82f6", "bg": "rgba(59,130,246,.08)", "border": "rgba(59,130,246,.3)",
     "tools": ["nmap","nuclei","zap","sqlmap","sliver","bloodhound","kafka","defectdojo","report"],
     "yaml": "presets/red-blue-exercise.yaml",
     "phases": ["偵察","掃描","Web攻擊","注入","C2植入","AD分析","事件流","歸檔","報告"]},
    {"id": "scb-full", "name": "⚙️ secureCodeBox 全掃", "desc": "K8s 原生掃描，適合 CI/CD 自動化整合",
     "color": "#6366f1", "bg": "rgba(99,102,241,.08)", "border": "rgba(99,102,241,.3)",
     "tools": ["scb-nmap","scb-nuclei","scb-zap","scb-trivy","scb-semgrep","defectdojo","report"],
     "yaml": "presets/scb-full.yaml",
     "phases": ["網路掃描","漏洞模板","DAST","容器掃描","SAST","歸檔","報告"]},
]

TOOLS = [
    {"id":"nmap",       "name":"Nmap",            "profile":"scan",    "container":"docker-nmap-1",      "port":None,  "url":None,                     "desc":"網路探索與埠掃描",        "category":"scan",
     "detail":"Phase A-1：資產盤點。掃描目標子網路，識別開放服務與作業系統指紋。",
     "cmds":["nmap -sV -sC -p- {target}","nmap -sU --top-ports 100 {target}","nmap --script vuln {target}"],"docs":"https://nmap.org/book/"},
    {"id":"nuclei",     "name":"Nuclei",          "profile":"scan",    "container":"docker-nuclei-1",    "port":None,  "url":None,                     "desc":"CVE/漏洞模板掃描引擎",   "category":"scan",
     "detail":"Phase A-2：漏洞發現。承接 Nmap 結果，對開放服務執行 5000+ 漏洞模板。",
     "cmds":["nuclei -u {target} -t exposures/ -t cves/","nuclei -u {target} -t misconfiguration/"],"docs":"https://docs.projectdiscovery.io/tools/nuclei"},
    {"id":"zap",        "name":"OWASP ZAP",       "profile":"redteam", "container":"docker-zap-1",       "port":8091,  "url":"http://localhost:8091",  "desc":"Web 代理與自動化掃描",   "category":"web",
     "detail":"DAST 動態應用安全測試。支援 Spider、Active Scan、API 模糊測試。",
     "cmds":["zap-baseline.py -t {target}","zap-full-scan.py -t {target} -r report.html"],"docs":"https://www.zaproxy.org/docs/"},
    {"id":"sqlmap",     "name":"SQLMap",          "profile":"redteam", "container":"docker-sqlmap-1",    "port":None,  "url":None,                     "desc":"自動化 SQL 注入檢測",    "category":"web",
     "detail":"偵測並利用 SQL 注入漏洞，支援 MySQL/MSSQL/PostgreSQL/Oracle。",
     "cmds":["sqlmap -u '{target}/api/v1/user?id=1' --dbs","sqlmap -u {target} --forms --crawl=3"],"docs":"https://sqlmap.org/"},
    {"id":"gobuster",   "name":"Gobuster / ffuf", "profile":"redteam", "container":"docker-gobuster-1",  "port":None,  "url":None,                     "desc":"目錄爆破與路徑枚舉",     "category":"web",
     "detail":"暴力枚舉隱藏路徑、API endpoint、子網域。",
     "cmds":["gobuster dir -u {target} -w /wordlists/common.txt"],"docs":"https://github.com/OJ/gobuster"},
    {"id":"nikto",      "name":"Nikto",           "profile":"redteam", "container":"docker-nikto-1",     "port":None,  "url":None,                     "desc":"Web 伺服器弱點掃描",     "category":"web",
     "detail":"快速掃描 Web 伺服器錯誤配置、過期軟體、危險檔案。",
     "cmds":["nikto -h {target}","nikto -h {target} -ssl"],"docs":"https://cirt.net/Nikto2"},
    {"id":"sliver",     "name":"Sliver C2",       "profile":"c2",      "container":"docker-sliver-1",    "port":31337, "url":"http://localhost:31337", "desc":"Go 語言木馬 C2 框架",    "category":"c2",
     "detail":"Phase B/C：突破與後滲透控制。支援 mTLS/HTTP/DNS/WireGuard。",
     "cmds":["sliver-server","sliver > generate --mtls {lhost} --os linux --arch amd64 --name agent"],"docs":"https://github.com/BishopFox/sliver"},
    {"id":"metasploit", "name":"Metasploit",      "profile":"c2",      "container":"docker-msf-1",       "port":55552, "url":None,                     "desc":"業界標準漏洞利用框架",   "category":"c2",
     "detail":"2000+ exploit 模組，支援 payload 生成、post-exploitation、pivoting。",
     "cmds":["msfconsole","msf > use exploit/multi/handler"],"docs":"https://metasploit.com/"},
    {"id":"bloodhound", "name":"BloodHound",      "profile":"platform","container":"docker-bloodhound-1","port":7474,  "url":"http://localhost:7474",  "desc":"AD 攻擊路徑視覺化",      "category":"ad",
     "detail":"分析 Active Directory 權限關係，找出最短提權路徑。",
     "cmds":["SharpHound.exe -c All","neo4j console","bloodhound"],"docs":"https://github.com/BloodHoundAD/BloodHound"},
    {"id":"defectdojo", "name":"DefectDojo",      "profile":"reporting","container":"docker-defectdojo-1","port":8001, "url":"http://localhost:8001",  "desc":"漏洞管理與報告平台",     "category":"platform",
     "detail":"匯入掃描結果，管理 findings 生命週期，整合 CI/CD pipeline。",
     "cmds":["curl http://localhost:8001/api/v2/findings/"],"docs":"https://defectdojo.com/"},
    {"id":"faraday",    "name":"Faraday",         "profile":"platform","container":"docker-faraday-1",   "port":5985,  "url":"http://localhost:5985",  "desc":"協作式滲透測試管理",     "category":"platform",
     "detail":"多人協作滲透測試工作台，彙整所有工具輸出。",
     "cmds":["faraday-client"],"docs":"https://faradaysec.com/"},
    {"id":"elasticsearch","name":"Elasticsearch", "profile":"platform","container":"docker-elasticsearch-1","port":9200,"url":"http://localhost:9200","desc":"全文搜尋與日誌索引",     "category":"platform",
     "detail":"搜尋引擎，用於索引掃描結果、事件日誌、漏洞資料。",
     "cmds":["curl http://localhost:9200/_cluster/health"],"docs":"https://elastic.co/"},
    {"id":"kibana",     "name":"Kibana",          "profile":"platform","container":"docker-kibana-1",    "port":5601,  "url":"http://localhost:5601",  "desc":"資料視覺化儀表板",       "category":"platform",
     "detail":"與 Elasticsearch 整合，視覺化掃描趨勢、告警分析。",
     "cmds":["open http://localhost:5601"],"docs":"https://elastic.co/kibana"},
    {"id":"crapi",      "name":"crAPI (靶機)",    "profile":"targets", "container":"docker-crapi-web-1", "port":8888,  "url":"http://localhost:8888",  "desc":"OWASP 官方 API 靶場",    "category":"target",
     "detail":"練習 OWASP API Top 10 的官方靶場，含 BOLA/BFLA/Mass Assignment 等漏洞。",
     "cmds":["curl http://localhost:8888/identity/api/auth/login"],"docs":"https://github.com/OWASP/crAPI"},
    {"id":"dvwa",       "name":"DVWA (靶機)",     "profile":"targets", "container":"docker-dvwa-1",      "port":8080,  "url":"http://localhost:8080",  "desc":"Web 漏洞練習環境",       "category":"target",
     "detail":"涵蓋 SQL Injection、XSS、CSRF、File Upload 等 Web 漏洞的練習平台。",
     "cmds":["open http://localhost:8080"],"docs":"https://dvwa.co.uk/"},
]


def _container_running(name: str) -> bool:
    try:
        r = subprocess.run(["docker", "inspect", "--format", "{{.State.Running}}", name],
                           capture_output=True, text=True, timeout=3)
        return r.stdout.strip() == "true"
    except Exception:
        return False


@bp.route("/api/presets")
def api_presets():
    return jsonify(TOOL_PRESETS)


@bp.route("/api/targets")
def api_targets():
    targets = [t for t in TOOLS if t.get("category") == "target" and t.get("url")]
    return jsonify([{"id": t["id"], "name": t["name"], "url": t["url"], "desc": t["desc"]}
                    for t in targets])


@bp.route("/api/tools")
def api_tools():
    return jsonify([{**t, "running": _container_running(t["container"])} for t in TOOLS])


@bp.route("/api/tool/<tid>/start", methods=["POST"])
def api_tool_start(tid: str):
    tool = next((t for t in TOOLS if t["id"] == tid), None)
    if not tool:
        return jsonify({"error": "not found"}), 404
    try:
        subprocess.Popen(
            ["docker", "compose", "--profile", tool["profile"], "up", "-d", tool["id"]],
            cwd=DOCKER_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return jsonify({"ok": True, "msg": f"啟動 {tool['name']} 中..."})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@bp.route("/api/tool/<tid>/stop", methods=["POST"])
def api_tool_stop(tid: str):
    tool = next((t for t in TOOLS if t["id"] == tid), None)
    if not tool:
        return jsonify({"error": "not found"}), 404
    try:
        subprocess.run(["docker", "stop", tool["container"]], capture_output=True, timeout=10)
        return jsonify({"ok": True, "msg": f"已停止 {tool['name']}"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})
