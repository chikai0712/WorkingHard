#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

B = Path(__file__).resolve().parent
W = B.parents[2]
H, O = "127.0.0.1", 8765
A = W / "06-DevTools/automation/ai-rag"
D = W / "08-Database/DB-Automation/ai-rag"
P = D / "producer-artifacts"
Q = A / "query_local_rag.py"
LS = D / "db-summary-dataset.latest-scoped.example.json"
S = D / "db-summary-dataset.scanned.example.json"
F = B / "data" / "action-history.json"
MF = "action-manifest.json"
E = {"DRY_RUN": "true", "CI_PROVIDER": "local-control-plane", "TARGET_ENV": "dev"}
KEEP = 6
C={("cicd","run-source"):["bash",str(W/"02-Cloud-Deploy/automation/cicd/pipeline.sh")],("release","prepare-release"):["bash",str(W/"02-Cloud-Deploy/automation/release/release.sh"),"status"],("release","run-smoke"):["bash",str(W/"02-Cloud-Deploy/automation/release/release.sh"),"deploy"],("iac","run-plan"):["bash",str(W/"02-Cloud-Deploy/automation/iac/terraform_wrapper.sh"),".","plan"],("iac","run-post-apply"):["bash",str(W/"02-Cloud-Deploy/automation/iac/terraform_wrapper.sh"),".","apply-dry-run"],("db-ops","verify-backup"):["bash",str(W/"08-Database/DB-Automation/backup-recovery/verify_backup.sh")],("db-ops","run-precheck"):["bash",str(W/"08-Database/DB-Automation/migration/migrate.sh"),"precheck"],("db-ops","verify-monitoring"):["python3",str(W/"08-Database/DB-Automation/monitoring/k8s/generate_monitoring_summary.py")],("db-ops","run-network-check"):["python3",str(W/"08-Database/DB-Automation/ansible/generate_ansible_summary.py")]}
V={("db-ops","verify-backup"):{"SUMMARY_OUT":"db-backup-summary.local.json","EVIDENCE_OUT":"db-mysql-restore-evidence.local.json","DB_ENGINE":"mysql"},("db-ops","run-precheck"):{"SUMMARY_OUT":"db-migration-summary.local.json","EVIDENCE_OUT":"db-mysql-precheck-evidence.local.json","DB_ENGINE":"mysql"},("db-ops","verify-monitoring"):{"SUMMARY_OUT":"monitoring-summary.local.json","EVIDENCE_OUT":"monitoring-evidence.local.json","ALERT_NAME":"DBMonitoringHealthWarning"},("db-ops","run-network-check"):{"SUMMARY_OUT":"ansible-summary.f5.local.json","EVIDENCE_OUT":"ansible-evidence.f5.local.json","DEVICE_FAMILY":"f5"}}
R={("db-ops","verify-backup"):[{"command":["python3",str(W/"08-Database/DB-Automation/monitoring/k8s/generate_monitoring_summary.py")],"env":{"SUMMARY_OUT":"monitoring-summary.local.json","EVIDENCE_OUT":"monitoring-evidence.local.json","ALERT_NAME":"DBBackupSignalsWarning"}},{"command":["python3",str(W/"08-Database/DB-Automation/ansible/generate_ansible_summary.py")],"env":{"SUMMARY_OUT":"ansible-summary.f5.local.json","EVIDENCE_OUT":"ansible-evidence.f5.local.json","DEVICE_FAMILY":"f5"}}],("db-ops","run-precheck"):[{"command":["python3",str(W/"08-Database/DB-Automation/monitoring/k8s/generate_monitoring_summary.py")],"env":{"SUMMARY_OUT":"monitoring-summary.local.json","EVIDENCE_OUT":"monitoring-evidence.local.json","ALERT_NAME":"DBPrecheckSignalsWarning"}},{"command":["python3",str(W/"08-Database/DB-Automation/ansible/generate_ansible_summary.py")],"env":{"SUMMARY_OUT":"ansible-summary.f5.local.json","EVIDENCE_OUT":"ansible-evidence.f5.local.json","DEVICE_FAMILY":"f5"}}]}
M={"db-ops":[W/"08-Database/DB-Automation/ai-rag/db-backup-summary.example.json",W/"08-Database/DB-Automation/ai-rag/db-backup-summary.mysql.example.json",W/"08-Database/DB-Automation/ai-rag/db-migration-summary.example.json",W/"08-Database/DB-Automation/ai-rag/db-migration-summary.mysql.example.json",W/"08-Database/DB-Automation/ai-rag/db-monitoring-summary.example.json",W/"08-Database/DB-Automation/ai-rag/db-remediation-summary.example.json",W/"08-Database/DB-Automation/ai-rag/db-ansible-summary.example.json"]}
T={"cicd":{"module_id":"cicd","context_type":"runbook-qa","summary":"Source gate is the best first checkpoint; security findings should still be reviewed before promotion.","possible_causes":["Artifact metadata is ready","Security placeholders still need real scan integration"],"recommended_checks":["Review lint/test output","Review defensive scan placeholders","Confirm artifact traceability"],"related_artifacts":["02-Cloud-Deploy/automation/cicd/README.md"],"confidence":"medium","recommended_policy":"hold","recommendation_source":"static-mock","evidence_count":1,"artifact_count":1,"retrieval_evidence":[],"human_approval_required":True},"release":{"module_id":"release","context_type":"change-risk","summary":"Release manifest and approval flow should be reviewed before any smoke-test based promotion.","possible_causes":["Approval gate not fully automated","Post-deploy signals are placeholder based"],"recommended_checks":["Validate release manifest","Confirm exception governance","Review smoke-test plan"],"related_artifacts":["02-Cloud-Deploy/automation/release/README.md"],"confidence":"medium","recommended_policy":"hold","recommendation_source":"static-mock","evidence_count":1,"artifact_count":1,"retrieval_evidence":[],"human_approval_required":True},"iac":{"module_id":"iac","context_type":"change-risk","summary":"IaC changes should stay in review until policy and drift checks are connected to real evidence.","possible_causes":["Plan exists but policy review is placeholder","Post-apply verification is not yet real"],"recommended_checks":["Inspect terraform plan","Review policy boundary assumptions","Confirm drift baseline"],"related_artifacts":["02-Cloud-Deploy/automation/iac/README.md"],"confidence":"medium","recommended_policy":"hold","recommendation_source":"static-mock","evidence_count":1,"artifact_count":1,"retrieval_evidence":[],"human_approval_required":True}}
K={"db-ops":"backup migration monitoring remediation ansible warning hold review evidence","cicd":"source gate artifact traceability security review","release":"release manifest smoke test approval review","iac":"terraform plan policy drift baseline review"}
L = lambda p: json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
WJ = lambda p, x: (
    p.parent.mkdir(parents=True, exist_ok=True),
    p.write_text(json.dumps(x, indent=2, ensure_ascii=False), encoding="utf-8"),
)


def X(c, w, e=None):
    return subprocess.run(
        c,
        cwd=str(w),
        capture_output=True,
        text=True,
        timeout=20,
        env={**os.environ, **E, **(e or {})},
    )


def MP(scope):
    return P / scope / MF
def Y(m="", s="desc"):
 d = L(F)
 r = d if isinstance(d, list) else []
 if m:
  r = [i for i in r if i.get("moduleId") == m]
 return list(reversed(r)) if s == "asc" else r


def Z(m=""):
 r = [] if not m else [i for i in Y() if i.get("moduleId") != m]
 WJ(F, r)
 return r


def scope_dir(action_id):
 ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
 session = f"session-{ts[:8]}"
 action = f"action-{action_id}-{ts}"
 d = P / session / action
 d.mkdir(parents=True, exist_ok=True)
 return d, f"{session}/{action}"


def cleanup():
 if not P.exists():
  return
 sessions = sorted([p for p in P.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
 for extra in sessions[KEEP:]:
  shutil.rmtree(extra, ignore_errors=True)
def scoped_env(key, d):
 env = {"ARTIFACT_DIR": str(d)}
 base = V.get(key, {})
 for k, v in base.items():
  env[k] = str(d / v) if k in {"SUMMARY_OUT", "EVIDENCE_OUT"} else v
 return env


def run_steps(steps, d):
 out = []
 for step in steps:
  env = {"ARTIFACT_DIR": str(d)}
  for k, v in step.get("env", {}).items():
   env[k] = str(d / v) if k in {"SUMMARY_OUT", "EVIDENCE_OUT"} else v
  r = X(step["command"], W, env)
  out.append({"command": step["command"], "returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr})
 return out
def G(m, a):
 names = []
 for env in [V.get((m, a), {})] + [i.get("env", {}) for i in R.get((m, a), [])]:
  for k in ("SUMMARY_OUT", "EVIDENCE_OUT"):
   if env.get(k):
    names.append(Path(env[k]).name)
 return sorted(set(names))


def U(m, sources=None, scope=""):
 q = K.get(m)
 if not q or not Q.exists():
  return []
 cmd = ["python3", str(Q), "--include-evidence", "--top-k", "5"]
 if scope:
  cmd.append("--scoped-only")
 r = X(cmd + q.split(), A)
 if r.returncode != 0:
  return []
 try:
  it = json.loads(r.stdout or "[]")
 except json.JSONDecodeError:
  return []
 meta = L(LS) or L(S)
 meta = {i.get("source_file"): i for i in meta} if isinstance(meta, list) else {}
 if sources:
  it = [i for i in it if i.get("path") in sources]
 if scope:
  it = [i for i in it if meta.get(i.get("path"), {}).get("artifact_scope", "").startswith(scope)]
 return [{"path": i.get("path", "unknown"), "record_type": i.get("record_type", "unknown"), "score": i.get("score", 0), "summary": i.get("summary", "") or i.get("text", "")[:160], "schema_file": meta.get(i.get("path"), {}).get("schema_file"), "artifact_source": meta.get(i.get("path"), {}).get("source_file", i.get("path", "unknown"))} for i in it[:3]]


def MAN(scope=""):
 m = L(MP(scope)) if scope else None
 return m if isinstance(m, dict) else {}
def REC(m, a="", latest=False, scope=""):
 if m in T and m != "db-ops":
  return T[m]
 rows = Y(m)
 scope = scope or (rows[0].get("actionScope", "") if latest and rows else "")
 manifest = MAN(scope)
 sources = G(m, a) if a else (manifest.get("artifact_sources") or (rows[0].get("artifactSources", []) if latest and rows else []))
 sums = [p for x in M.get(m, []) if isinstance((p := L(x)), dict)]
 sc = L(LS) if latest else L(S)
 sc = sc if isinstance(sc, list) else []
 if latest:
  sc = [i for i in sc if i.get("module") in {"backup-recovery", "migration", "monitoring/k8s", "ansible", "remediation"}]
 elif scope:
  sc = [i for i in sc if i.get("artifact_scope", "").startswith(scope)]
 elif sources:
  sc = [i for i in sc if i.get("source_file") in sources]
 else:
  sc = [i for i in sc if i.get("module") in {"backup-recovery", "migration", "monitoring/k8s", "ansible", "remediation"}]
 if not sums and not sc:
  return None
 causes, checks, arts, pol = [], [], [], "pass"
 if not latest and not scope and not sources:
  for i in sums:
   causes.append(i.get("summary", ""))
   checks += i.get("recommended_checks", [])
   arts.append(f"summary::{i.get('module', 'unknown')}")
   if i.get("recommended_policy") in {"hold", "block", "rollback", "fallback"}:
    pol = i.get("recommended_policy")
 for i in sc:
  p = i.get("summary", {})
  causes.append(p.get("summary", ""))
  checks += p.get("recommended_checks", [])
  arts.append(i.get("source_file", "unknown"))
  if p.get("recommended_policy") in {"hold", "block", "rollback", "fallback"}:
   pol = p.get("recommended_policy")
 return {"module_id": m, "context_type": "local-summary-analysis", "summary": "Recommendation generated from local summary artifacts. Review summarized evidence before privileged actions.", "possible_causes": causes, "recommended_checks": checks, "related_artifacts": arts, "confidence": "medium", "recommended_policy": pol, "recommendation_source": "latest-scoped-artifacts" if latest else ("local-summary-artifacts-scoped" if (scope or sources) else "local-summary-artifacts"), "evidence_count": (0 if latest else len(sums)) + len(sc), "artifact_count": len(arts), "retrieval_evidence": U(m, sources or None, scope), "human_approval_required": True, "scoped_artifacts": sources, "action_scope": scope, "manifest": manifest}
def DB(m, a, d, scope):
 steps = R.get((m, a), []) + [
  {"command": ["python3", str(D / "validate_db_summary.py")]},
  {"command": ["python3", str(D / "ingest_db_summaries.py"), "--scan-dir", str(P), "--scope-prefix", scope, "--include-evidence", "--scoped-only", "--output", str(LS)]},
  {"command": ["python3", str(D / "ingest_db_summaries.py"), "--scan-dir", str(P), "--include-evidence", "--output", str(S)]},
 ]
 return run_steps(steps, d)


def WM(module_id, action_id, scope, command, artifact_sources, result, refresh):
 manifest = {"module_id": module_id, "action_id": action_id, "action_scope": scope, "manifest_path": str(MP(scope).relative_to(W)), "artifact_sources": artifact_sources, "command": command, "returncode": result.returncode, "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), "refresh_steps": [{"command": item.get("command"), "returncode": item.get("returncode")} for item in refresh]}
 WJ(MP(scope), manifest)
 return manifest
class N(SimpleHTTPRequestHandler):
 def __init__(self, *a, **k):
  super().__init__(*a, directory=str(B), **k)

 def J(self, s, p):
  b = json.dumps(p, ensure_ascii=False).encode("utf-8")
  self.send_response(s)
  self.send_header("Content-Type", "application/json; charset=utf-8")
  self.send_header("Content-Length", str(len(b)))
  self.end_headers()
  self.wfile.write(b)

 def do_GET(self):
  p = urlparse(self.path)
  q = parse_qs(p.query)
  if p.path == "/api/recommendations":
   r = REC(q.get("module_id", [""])[0], q.get("action_id", [""])[0], q.get("latest_only", ["false"])[0] == "true", q.get("action_scope", [""])[0])
   return self.J(HTTPStatus.OK, r) if r else self.J(HTTPStatus.NOT_FOUND, {"error": "recommendation not found"})
  if p.path == "/api/action-history":
   return self.J(HTTPStatus.OK, Y(q.get("module_id", [""])[0], q.get("sort", ["desc"])[0]))
  return super().do_GET()

 def do_POST(self):
  raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
  try:
   p = json.loads(raw.decode("utf-8")) if raw else {}
  except json.JSONDecodeError:
   return self.J(HTTPStatus.BAD_REQUEST, {"error": "invalid json"})
  if self.path == "/api/action-history":
   r = [p, *Y()][:20]
   WJ(F, r)
   return self.J(HTTPStatus.OK, r)
  if self.path != "/api/actions":
   return self.J(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint"})
  k = (p.get("moduleId"), p.get("actionId"))
  c = C.get(k)
  if not c:
   return self.J(HTTPStatus.BAD_REQUEST, {"error": "action not allowed", "moduleId": p.get("moduleId"), "actionId": p.get("actionId")})
  d, scope = scope_dir(p.get("actionId"))
  cleanup()
  r = X(c, W, scoped_env(k, d))
  extra = DB(*k, d, scope) if p.get("moduleId") == "db-ops" else []
  sources = G(*k)
  manifest = WM(p.get("moduleId"), p.get("actionId"), scope, c, sources, r, extra)
  return self.J(HTTPStatus.OK, {"moduleId": p.get("moduleId"), "actionId": p.get("actionId"), "command": c, "returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr, "mode": "local-dry-run-adapter", "action_scope": scope, "artifact_sources": sources, "manifest": manifest, "post_action_refresh": extra})

 def do_DELETE(self):
  p = urlparse(self.path)
  if p.path != "/api/action-history":
   return self.J(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint"})
  return self.J(HTTPStatus.OK, Z(parse_qs(p.query).get("module_id", [""])[0]))

def main():
 WJ(F, Y())
 s = ThreadingHTTPServer((H, O), N)
 print(f"[control-plane] serving {B} at http://{H}:{O}")
 s.serve_forever()

if __name__ == "__main__":
 main()
