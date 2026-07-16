"""
secureCodeBox client — Flask 透過 k8s API 提交 Scan CRD 並讀取狀態
"""
import json
import subprocess
import time
import uuid
from urllib.parse import urlparse

from kubernetes import client, config
from minio import Minio

SCB_NAMESPACE = "securecodebox-system"
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS = "admin"
MINIO_SECRET = "iWdbGMmiWUDpQtlGe89HIKaOLAV7ve9a"
MINIO_BUCKET = "securecodebox"
TERMINAL_STATES = {"Done", "Errored", "Aborted"}


def _k8s_custom():
    try:
        config.load_incluster_config()
    except Exception:
        config.load_kube_config()
    return client.CustomObjectsApi()


def _normalize_target(target: str) -> tuple[str, str]:
    """回傳 (nmap_target, nuclei_url)"""
    target = target.strip()
    if "://" not in target:
        return target, f"https://{target}"
    parsed = urlparse(target)
    host = parsed.netloc or parsed.path
    nmap_target = host.split(":")[0]
    return nmap_target, target


def _tags_for_templates(templates: str) -> str:
    mapping = {
        "exposure": "exposure",
        "gambling": "exposure",
        "cve": "cve",
        "misconfig": "misconfiguration",
    }
    return mapping.get(templates, templates)


def submit_scan(scan_type: str, parameters: list) -> str:
    """提交 secureCodeBox Scan CRD，回傳 scan name"""
    api = _k8s_custom()
    scan_name = f"{scan_type}-{uuid.uuid4().hex[:8]}"
    body = {
        "apiVersion": "execution.securecodebox.io/v1",
        "kind": "Scan",
        "metadata": {"name": scan_name, "namespace": SCB_NAMESPACE},
        "spec": {"scanType": scan_type, "parameters": parameters},
    }
    api.create_namespaced_custom_object(
        group="execution.securecodebox.io",
        version="v1",
        namespace=SCB_NAMESPACE,
        plural="scans",
        body=body,
    )
    return scan_name


def submit_nmap_scan(target: str) -> str:
    nmap_target, _ = _normalize_target(target)
    return submit_scan("nmap", [nmap_target])


def submit_nuclei_scan(target: str, templates: str = "exposure") -> str:
    _, nuclei_url = _normalize_target(target)
    tags = _tags_for_templates(templates)
    return submit_scan("nuclei", ["-u", nuclei_url, "-tags", tags])


def get_scan_status(scan_name: str) -> dict:
    """查詢 scan 狀態"""
    api = _k8s_custom()
    try:
        obj = api.get_namespaced_custom_object(
            group="execution.securecodebox.io",
            version="v1",
            namespace=SCB_NAMESPACE,
            plural="scans",
            name=scan_name,
        )
        status = obj.get("status", {})
        findings = status.get("findings", {})
        hook_statuses = status.get("orderedHookStatuses") or status.get("hookStatus") or []
        return {
            "scan_name": scan_name,
            "scan_type": obj.get("spec", {}).get("scanType"),
            "state": status.get("state", "Unknown"),
            "findings_count": findings.get("count", 0),
            "findings_by_severity": findings.get("severities", {}),
            "findings_by_category": findings.get("categories", {}),
            "finished_at": status.get("finishedAt"),
            "error_description": status.get("errorDescription"),
            "hook_statuses": hook_statuses,
            "finding_download_link": status.get("findingDownloadLink"),
        }
    except Exception as e:
        return {"scan_name": scan_name, "state": "Error", "error": str(e)}


def wait_for_scan(scan_name: str, timeout: int = 600, poll_interval: int = 5,
                  on_update=None) -> dict:
    """輪詢直到 scan 完成，可選 callback(status_dict)"""
    deadline = time.time() + timeout
    last_state = None
    while time.time() < deadline:
        status = get_scan_status(scan_name)
        state = status.get("state", "Unknown")
        if state != last_state and on_update:
            on_update(status)
            last_state = state
        if state in TERMINAL_STATES:
            if on_update and state != last_state:
                on_update(status)
            return status
        time.sleep(poll_interval)
    return {"scan_name": scan_name, "state": "Timeout", "error": f"超過 {timeout}s"}


def run_cascade_scan(target: str, templates: str = "exposure",
                     on_update=None) -> dict:
    """
    Nmap → Nuclei 級聯掃描。
    on_update(phase, status_dict) 用於即時 log。
    """
    def notify(phase: str, status: dict):
        if on_update:
            on_update(phase, status)

    notify("nmap", {"state": "Submitting", "scan_name": "", "findings_count": 0})
    nmap_name = submit_nmap_scan(target)
    notify("nmap", {"state": "Scanning", "scan_name": nmap_name, "findings_count": 0})

    nmap_status = wait_for_scan(
        nmap_name,
        on_update=lambda s: notify("nmap", s),
    )
    if nmap_status.get("state") not in ("Done", "Errored"):
        return {"ok": False, "phase": "nmap", "nmap": nmap_status}

    notify("nuclei", {"state": "Submitting", "scan_name": "", "findings_count": 0})
    nuclei_name = submit_nuclei_scan(target, templates)
    notify("nuclei", {"state": "Scanning", "scan_name": nuclei_name, "findings_count": 0})

    nuclei_status = wait_for_scan(
        nuclei_name,
        on_update=lambda s: notify("nuclei", s),
    )
    ok = nuclei_status.get("state") == "Done" or nuclei_status.get("findings_count", 0) > 0
    return {
        "ok": ok,
        "nmap": nmap_status,
        "nuclei": nuclei_status,
        "findings_count": nuclei_status.get("findings_count", 0),
    }


def ensure_minio_port_forward() -> bool:
    """確保本機 9001 可連 MinIO（供讀取 findings JSON）"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(1)
        sock.connect(("127.0.0.1", 9001))
        return True
    except OSError:
        pass
    finally:
        sock.close()

    subprocess.Popen(
        ["kubectl", "port-forward", "-n", "securecodebox-system",
         "svc/securecodebox-operator-minio", "9001:9001"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(10):
        time.sleep(1)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(1)
            sock.connect(("127.0.0.1", 9001))
            return True
        except OSError:
            pass
        finally:
            sock.close()
    return False


def get_findings(scan_name: str) -> list:
    """從 MinIO 下載 findings JSON"""
    status = get_scan_status(scan_name)
    if status.get("state") not in TERMINAL_STATES:
        return []

    if not ensure_minio_port_forward():
        return [{"error": "MinIO port-forward 無法建立"}]

    api = _k8s_custom()
    obj = api.get_namespaced_custom_object(
        group="execution.securecodebox.io",
        version="v1",
        namespace=SCB_NAMESPACE,
        plural="scans",
        name=scan_name,
    )
    scan_uid = obj["metadata"]["uid"]
    object_path = f"scan-{scan_uid}/findings.json"

    try:
        mc = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS,
                   secret_key=MINIO_SECRET, secure=False)
        data = mc.get_object(MINIO_BUCKET, object_path)
        return json.loads(data.read())
    except Exception as e:
        return [{"error": str(e)}]


def list_scans() -> list:
    """列出所有 scan"""
    api = _k8s_custom()
    result = api.list_namespaced_custom_object(
        group="execution.securecodebox.io",
        version="v1",
        namespace=SCB_NAMESPACE,
        plural="scans",
    )
    scans = []
    for item in result.get("items", []):
        status = item.get("status", {})
        findings = status.get("findings", {})
        params = item.get("spec", {}).get("parameters") or []
        scans.append({
            "name": item["metadata"]["name"],
            "scan_type": item["spec"]["scanType"],
            "target": params[1] if len(params) > 1 and params[0] == "-u" else (params[0] if params else ""),
            "state": status.get("state", "Unknown"),
            "findings_count": findings.get("count", 0),
            "created_at": item["metadata"]["creationTimestamp"],
        })
    return sorted(scans, key=lambda x: x["created_at"], reverse=True)


if __name__ == "__main__":
    print("=== 目前所有 Scans ===")
    for s in list_scans():
        print(f"  [{s['state']}] {s['name']} ({s['scan_type']}) → {s['target']} — {s['findings_count']} findings")
