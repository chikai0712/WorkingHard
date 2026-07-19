"""掃描工具 Docker image 清單，供 /api/images 路由使用。"""

IMAGE_CATALOG = [
    {
        "id":    "nmap",
        "name":  "Nmap",
        "desc":  "主機發現與連接埠掃描",
        "image": "instrumentisto/nmap",
        "tag":   "7.95",
    },
    {
        "id":    "nuclei",
        "name":  "Nuclei",
        "desc":  "基於模板的漏洞掃描器",
        "image": "projectdiscovery/nuclei",
        "tag":   "v3.11.0",
    },
    {
        "id":    "zap",
        "name":  "OWASP ZAP",
        "desc":  "Web 應用程式動態掃描",
        "image": "zaproxy/zap-stable",
        "tag":   "2.17.0",
    },
    {
        "id":    "pentest-tools",
        "name":  "Pentest Tools",
        "desc":  "SQLMap + Gobuster + Nikto 組合包",
        "image": "redsaas-pentest-tools",
        "tag":   "latest",
    },
]
