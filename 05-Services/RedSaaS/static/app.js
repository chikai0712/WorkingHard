const PIPE_STAGES = ["nmap","nuclei","defectdojo","report"];
let pollTimer = null, currentJobId = null;

const TOOL_PIPELINE_MAP = {
  nmap:      {label:"Nmap 資產盤點",   id:"pipe-nmap"},
  nuclei:    {label:"Nuclei 漏洞掃描", id:"pipe-nuclei"},
  zap:       {label:"ZAP 掃描",        id:"pipe-zap"},
  sqlmap:    {label:"SQLMap 注入",     id:"pipe-sqlmap"},
  gobuster:  {label:"Gobuster 枚舉",   id:"pipe-gobuster"},
  nikto:     {label:"Nikto 掃描",      id:"pipe-nikto"},
  defectdojo:{label:"DefectDojo 匯入", id:"pipe-defectdojo"},
  report:    {label:"AI 報告生成",     id:"pipe-report"},
};

let activePipelineTools = ["nmap","nuclei","defectdojo","report"];

function updatePipeline() {
  const checked = [...document.querySelectorAll("#tool-picker input:checked")].map(el => el.value);
  activePipelineTools = checked;
  const pipeline = document.getElementById("pipeline-dynamic");
  if (!pipeline) return;
  pipeline.innerHTML = checked.map((tool, i) => {
    const info = TOOL_PIPELINE_MAP[tool] || {label: tool, id: "pipe-"+tool};
    const arrow = i < checked.length - 1 ? '<div class="pipe-arrow" id="arrow-'+(i+1)+'">→</div>' : "";
    return '<div class="pipe-node" id="'+info.id+'">'+info.label+'</div>' + arrow;
  }).join("");
}
const ALL_TABS = ["scan","history","findings","status","schedules","tools","reports","hub","images","ai","c2","ad","events","lab"];
const TAB_TITLES = {scan:"新增掃描",history:"掃描歷史",findings:"Findings",status:"系統狀態",schedules:"排程掃描",tools:"工具中心",reports:"報表中心",hub:"整合中心",images:"Image 倉庫",ai:"AI 攻擊劇本",c2:"C2 控制台",ad:"AD 攻擊路徑",events:"事件流",lab:"服務控制台"};
let findingFilter = "", findingOffset = 0, findingTotal = 0;
const FINDING_LIMIT = 30;

function switchTab(name) {
  ALL_TABS.forEach(t => {
    const el = document.getElementById("nav-"+t);
    if (el) el.classList.toggle("active", t===name);
  });
  document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
  document.getElementById("tab-"+name).classList.add("active");
  const title = document.getElementById("topbar-title");
  if (title) title.textContent = TAB_TITLES[name] || name;
  if (name==="history") loadHistory();
  if (name==="findings") { findingOffset=0; loadFindings(); }
  if (name==="status") loadStatus();
  if (name==="schedules") loadSchedules();
  if (name==="tools") loadTools();
  if (name==="reports") { loadReports(); loadAiReports(); }
  if (name==="hub") loadHub();
  if (name==="images") loadImages();
  if (name==="lab") loadLabGroups();
}


function setPipeState(stage, state) {
  const info = TOOL_PIPELINE_MAP[stage];
  const nodeId = info ? info.id : "pipe-"+stage;
  const node = document.getElementById(nodeId);
  if (!node) return;
  node.className = "pipe-node" + (state ? " "+state : "");
  const idx = activePipelineTools.indexOf(stage);
  if (idx > 0) {
    const arrow = document.getElementById("arrow-"+idx);
    if (arrow) arrow.className = "pipe-arrow" + (state==="done" ? " done" : "");
  }
}

function setCurrentTool(stage) {
  activePipelineTools.forEach(t => {
    const info = TOOL_PIPELINE_MAP[t];
    const node = document.getElementById(info ? info.id : "pipe-"+t);
    if (node) node.classList.remove("current");
  });
  const info = TOOL_PIPELINE_MAP[stage];
  const node = document.getElementById(info ? info.id : "pipe-"+stage);
  if (node) node.classList.add("current");
}

function resetPipeline() {
  activePipelineTools.forEach(s => setPipeState(s, ""));
  document.getElementById("severity-stats").style.display = "none";
  ["sev-critical","sev-high","sev-medium","sev-low","sev-info"].forEach(id => {
    document.getElementById(id).textContent = "0";
  });
}

function updateSeverity(severities) {
  if (!severities) return;
  const shown = Object.values(severities).some(v => v > 0);
  if (!shown) return;
  document.getElementById("severity-stats").style.display = "flex";
  const map = {Critical:"sev-critical",High:"sev-high",Medium:"sev-medium",Low:"sev-low",Informational:"sev-info",Info:"sev-info"};
  for (const [k, id] of Object.entries(map)) {
    if (severities[k] !== undefined) document.getElementById(id).textContent = severities[k];
  }
}

function inferPipeline(logs, data) {
  const t = logs.join(" ");
  if (data.status === "done") {
    PIPE_STAGES.slice(0, data.report_name ? 4 : 3).forEach(s => setPipeState(s, "done"));
    return;
  }
  if (t.includes("報告完成")) { PIPE_STAGES.forEach(s => setPipeState(s, "done")); return; }
  if (t.includes("匯入成功") || t.includes("Engagement ID：")) {
    ["nmap","nuclei","defectdojo"].forEach(s => setPipeState(s, "done"));
    setPipeState("report", "active"); return;
  }
  if (t.includes("Nuclei 完成") || t.includes("[NUCLEI]") || t.includes("Nuclei 掃描")) {
    setPipeState("nmap", "done"); setPipeState("nuclei", "active"); return;
  }
  if (t.includes("[NMAP]") || t.includes("Nmap")) { setPipeState("nmap", "active"); }
}

async function startScan() {
  const target = document.getElementById("target").value.trim();
  const name = document.getElementById("name").value.trim();
  if (!target || !name) { alert("請填寫目標 URL 和專案名稱"); return; }
  document.getElementById("scan-btn").disabled = true;
  document.getElementById("stop-btn").style.display = "inline-block";
  document.getElementById("log-box").textContent = "提交任務中...";
  document.getElementById("result-links").innerHTML = "";
  resetPipeline();
  if (activePipelineTools.length > 0) setCurrentTool(activePipelineTools[0]);
  const badge = document.getElementById("status-badge");
  badge.className = "badge badge-running"; badge.textContent = "執行中";
  const resp = await fetch("/api/scan", {
    method: "POST", headers: {"Content-Type":"application/json"},
    body: JSON.stringify({
      target, name,
      templates: document.getElementById("templates").value,
      engine: document.getElementById("engine").value,
      with_report: document.getElementById("with-report").checked,
      tools: activePipelineTools
    })
  });
  const data = await resp.json();
  currentJobId = data.job_id;
  pollTimer = setInterval(pollStatus, 1500);
}

async function pollStatus() {
  if (!currentJobId) return;
  const resp = await fetch("/api/status/" + currentJobId);
  const data = await resp.json();
  const box = document.getElementById("log-box");
  box.innerHTML = data.logs.map(line => {
    if (line.includes("[錯誤]") || line.includes("ERR")) return '<div class="err">'+line+'</div>';
    if (line.includes("[警告]") || line.includes("WRN")) return '<div class="warn">'+line+'</div>';
    if (line.includes("\u2713") || line.includes("完成"))    return '<div class="ok">'+line+'</div>';
    return '<div>'+line+'</div>';
  }).join("");
  box.scrollTop = box.scrollHeight;
  inferPipeline(data.logs, data);
  if (data.scb_scans) updateSeverity(data.scb_scans.severities);

  if (data.status === "done") {
    clearInterval(pollTimer);
    document.getElementById("scan-btn").disabled = false;
    document.getElementById("stop-btn").style.display = "none";
    const b = document.getElementById("status-badge");
    b.className = "badge badge-done"; b.textContent = "完成";
    const links = document.getElementById("result-links");
    links.innerHTML = "";
    if (data.findings_count != null)
      links.innerHTML += '<span style="color:#86efac;font-size:.85rem">Findings: '+data.findings_count+'</span>';
    if (data.dd_url)
      links.innerHTML += '<a href="'+data.dd_url+'" target="_blank">在 DefectDojo 查看 →</a>';
    if (data.report_name) {
      links.innerHTML += '<a href="/api/download/'+currentJobId+'">下載報告 ↓</a>';
      links.innerHTML += '<a href="#" onclick="previewReport();return false">預覽報告 👁</a>';
    }
  } else if (data.status === "failed") {
    clearInterval(pollTimer);
    document.getElementById("scan-btn").disabled = false;
    document.getElementById("stop-btn").style.display = "none";
    const b = document.getElementById("status-badge");
    b.className = "badge badge-failed"; b.textContent = "失敗";
  }
}

function copyLog() {
  const box = document.getElementById("log-box");
  const text = box.innerText || box.textContent;
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById("copy-log-btn");
    const orig = btn.textContent;
    btn.textContent = "✓ 已複製";
    btn.style.color = "#86efac";
    setTimeout(() => { btn.textContent = orig; btn.style.color = "#94a3b8"; }, 2000);
  }).catch(() => {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select(); document.execCommand("copy");
    document.body.removeChild(ta);
  });
}

async function stopScan() {
  if (!currentJobId || !confirm("確定要停止目前的掃描任務？")) return;
  await fetch("/api/stop/"+currentJobId, {method:"POST"});
  clearInterval(pollTimer);
  document.getElementById("scan-btn").disabled = false;
  document.getElementById("stop-btn").style.display = "none";
  const b = document.getElementById("status-badge");
  b.className = "badge badge-failed"; b.textContent = "已停止";
}

async function loadHistory() {
  const container = document.getElementById("history-table");
  container.innerHTML = '<div class="empty">載入中...</div>';
  try {
    const resp = await fetch("/api/scans");
    const scans = await resp.json();
    if (scans.error) { container.innerHTML = '<div class="empty">無法連線 K8s：'+scans.error+'</div>'; return; }
    if (!scans.length) { container.innerHTML = '<div class="empty">尚無掃描記錄</div>'; return; }
    let totH=0, totM=0, totDone=0;
    scans.forEach(s => {
      const sev = s.findings_by_severity || {};
      totH += (sev.High||0) + (sev.Critical||0);
      totM += (sev.Medium||0);
      if (s.state==="Done") totDone++;
    });
    document.getElementById("stat-total").textContent = scans.length;
    document.getElementById("stat-high").textContent  = totH || "-";
    document.getElementById("stat-med").textContent   = totM || "-";
    document.getElementById("stat-done").textContent  = totDone;
    let html = '<table><thead><tr><th>名稱</th><th>類型</th><th>目標</th><th>狀態</th><th>Findings</th><th>時間</th></tr></thead><tbody>';
    for (const s of scans) {
      const ts = s.created_at
        ? new Date(s.created_at).toLocaleString("zh-TW",{month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"})
        : "-";
      const sev = s.findings_by_severity || {};
      let sevHtml = "";
      if (sev.Critical) sevHtml += '<span class="badge badge-high" style="margin-right:.2rem">C:'+sev.Critical+'</span>';
      if (sev.High)     sevHtml += '<span class="badge badge-high" style="margin-right:.2rem">H:'+sev.High+'</span>';
      if (sev.Medium)   sevHtml += '<span class="badge badge-med"  style="margin-right:.2rem">M:'+sev.Medium+'</span>';
      if (sev.Low)      sevHtml += '<span class="badge badge-info">L:'+sev.Low+'</span>';
      if (!sevHtml) sevHtml = s.findings_count
        ? String(s.findings_count)
        : '<span style="color:#475569">-</span>';
      html += '<tr>'
        + '<td style="font-family:monospace;color:#93c5fd;font-size:.8rem">'+s.name+'</td>'
        + '<td><span style="color:#64748b">'+s.scan_type+'</span></td>'
        + '<td style="color:#cbd5e1;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+s.target+'</td>'
        + '<td><span class="scan-state state-'+s.state+'">'+s.state+'</span></td>'
        + '<td>'+sevHtml+'</td>'
        + '<td style="color:#475569;font-size:.8rem">'+ts+'</td>'
        + '</tr>';
    }
    html += '</tbody></table>';
    container.innerHTML = html;
  } catch(e) {
    container.innerHTML = '<div class="empty">載入失敗：'+e.message+'</div>';
  }
}

async function previewReport() {
  const resp = await fetch("/api/preview/"+currentJobId);
  const data = await resp.json();
  if (data.error) { alert("預覽失敗："+data.error); return; }
  let html = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">'
    + '<span style="font-weight:600;color:#f1f5f9">'+data.name+'</span>'
    + '<button onclick="document.getElementById(&quot;preview-card&quot;).style.display=&quot;none&quot;"'
    + ' style="background:#334155;color:#94a3b8;padding:.3rem .8rem;border-radius:6px;border:none;cursor:pointer">關閉</button></div>';
  for (const b of data.blocks) {
    if (b.type==="h1")      html += '<h2 style="color:#f1f5f9;font-size:1.2rem;margin:1.5rem 0 .5rem">'+b.text+'</h2>';
    else if (b.type==="h2") html += '<h3 style="color:#93c5fd;font-size:1rem;margin:1.2rem 0 .4rem">'+b.text+'</h3>';
    else if (b.type==="h3") html += '<h4 style="color:#7dd3fc;font-size:.9rem;margin:1rem 0 .3rem">'+b.text+'</h4>';
    else html += '<p style="color:#cbd5e1;font-size:.85rem;line-height:1.7;margin-bottom:.5rem">'+(b.html||b.text)+'</p>';
  }
  const card = document.getElementById("preview-card");
  document.getElementById("preview-body").innerHTML = html;
  card.style.display = "block";
  card.scrollIntoView({behavior:"smooth"});
}

// ── Findings ──────────────────────────────────────────
function setFindingFilter(sev) {
  findingFilter = sev; findingOffset = 0;
  document.querySelectorAll(".filter-btn").forEach(b => {
    b.classList.toggle("active", b.textContent.replace("Info","Informational")===sev || (sev==="" && b.textContent==="全部"));
  });
  loadFindings();
}

async function loadFindings() {
  const container = document.getElementById("findings-table");
  container.innerHTML = '<div class="empty">載入中...</div>';
  try {
    const params = new URLSearchParams({limit: FINDING_LIMIT, offset: findingOffset});
    if (findingFilter) params.set("severity", findingFilter);
    const resp = await fetch("/api/findings?"+params);
    const data = await resp.json();
    if (data.error) { container.innerHTML = '<div class="empty">無法連線 DefectDojo：'+data.error+'</div>'; return; }
    findingTotal = data.count || 0;
    const results = data.results || [];
    if (!results.length) { container.innerHTML = '<div class="empty">無 findings</div>'; renderFindingPagination(); return; }
    let html = '<table><thead><tr><th>標題</th><th>嚴重度</th><th>CVE</th><th>狀態</th><th>測試</th></tr></thead><tbody>';
    for (const f of results) {
      const sevClass = "sev-"+(f.severity||"Info");
      const cve = (f.cve_references||"").split(",")[0] || "-";
      const active = f.active ? '<span style="color:#86efac">Active</span>' : '<span style="color:#475569">Closed</span>';
      html += '<tr class="finding-row">'
        + '<td title="'+f.title+'">'+f.title+'</td>'
        + '<td><span class="sev-tag '+sevClass+'">'+(f.severity||"Info")+'</span></td>'
        + '<td style="font-size:.78rem;color:#64748b">'+cve+'</td>'
        + '<td>'+active+'</td>'
        + '<td style="font-size:.78rem;color:#475569">#'+f.test+'</td>'
        + '</tr>';
    }
    html += '</tbody></table>';
    container.innerHTML = html;
    renderFindingPagination();
  } catch(e) {
    container.innerHTML = '<div class="empty">載入失敗：'+e.message+'</div>';
  }
}

function renderFindingPagination() {
  const pg = document.getElementById("findings-pagination");
  const pages = Math.ceil(findingTotal / FINDING_LIMIT);
  const cur = Math.floor(findingOffset / FINDING_LIMIT);
  if (pages <= 1) { pg.innerHTML = ""; return; }
  let html = "";
  for (let i = 0; i < pages; i++) {
    const active = i===cur ? "border-color:#3b82f6;color:#60a5fa;background:#1e3a5f;" : "";
    html += '<button style="padding:.3rem .7rem;border-radius:5px;border:1px solid #334155;background:#0f172a;color:#94a3b8;cursor:pointer;'+active+'" onclick="findingOffset='+i*FINDING_LIMIT+';loadFindings()">'+(i+1)+'</button>';
  }
  pg.innerHTML = '<span style="font-size:.8rem;color:#64748b;margin-right:.5rem">共 '+findingTotal+' 筆</span>'+html;
}

// ── Status ────────────────────────────────────────────
async function loadStatus() {
  const setIndicator = (id, ok, label, meta) => {
    const el = document.getElementById("status-"+id);
    const dotClass = ok===null ? "dot-gray" : ok ? "dot-green" : "dot-red";
    el.innerHTML = '<span class="dot '+dotClass+'"></span>'+label;
    const m = document.getElementById("status-"+id+"-meta");
    if (m) m.textContent = meta||"";
  };
  setIndicator("dd","null","檢查中...");
  setIndicator("k8s",null,"檢查中...");
  try {
    const resp = await fetch("/api/status");
    const data = await resp.json();
    const dd = data.defectdojo||{};
    setIndicator("dd", dd.ok, dd.ok?"連線正常":"連線失敗", dd.ok?"API 回應 200":(dd.error||"HTTP "+dd.code));
    const k8s = data.k8s||{};
    setIndicator("k8s", k8s.ok, k8s.ok?"叢集正常":"連線失敗", k8s.ok?"Scan 數量："+k8s.scan_count:(k8s.error||""));
    const minio = data.minio||{};
    document.getElementById("status-minio").innerHTML = '<span class="dot '+(minio.ok?"dot-green":"dot-red")+'"></span>'+(minio.ok?"運行中":"無法連線");
    const docker = data.docker||{};
    document.getElementById("status-docker").innerHTML = '<span class="dot '+(docker.ok?"dot-green":"dot-red")+'"></span>'+(docker.ok?"運行中 "+((docker.containers||[]).length)+" 個容器":"無法連線");
    const list = document.getElementById("container-list");
    if (docker.containers&&docker.containers.length) {
      list.innerHTML = docker.containers.map(c => {
        const up = c.status.toLowerCase().includes("up");
        return '<div class="container-item"><span class="container-name">'+c.name+'</span><span class="container-status'+(up?" up":"")+'">'+c.status+'</span></div>';
      }).join("");
    } else {
      list.innerHTML = '<div class="empty" style="padding:.5rem">無容器資料</div>';
    }
  } catch(e) {
    setIndicator("dd", false, "載入失敗", e.message);
  }
}

// ── Schedules ─────────────────────────────────────────
async function loadSchedules() {
  const resp = await fetch("/api/schedules");
  const schedules = await resp.json();
  const container = document.getElementById("schedule-list");
  if (!schedules.length) { container.innerHTML = '<div class="empty">尚無排程</div>'; return; }
  container.innerHTML = schedules.map(s => {
    const on = s.enabled;
    return '<div class="schedule-item">'
      + '<div class="schedule-info">'
      + '<div class="schedule-name">'+s.name+'</div>'
      + '<div class="schedule-meta">目標：'+s.target+' ｜ 類型：'+s.templates+' ｜ Cron：'+s.cron+(s.last_run?' ｜ 上次：'+s.last_run:'')+'</div>'
      + '</div>'
      + '<div class="schedule-actions">'
      + `<button class="btn-sm ${on?"btn-toggle-on":"btn-toggle-off"}" onclick="toggleSchedule('${s.id}')">${on?"啟用中":"已停用"}</button>`
      + `<button class="btn-sm btn-del" onclick="deleteSchedule('${s.id}')">刪除</button>`
      + '</div></div>';
  }).join("");
}

async function addSchedule() {
  const name = document.getElementById("sch-name").value.trim();
  const target = document.getElementById("sch-target").value.trim();
  if (!name || !target) { alert("請填寫名稱和目標"); return; }
  await fetch("/api/schedules", {method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({name, target,
      templates: document.getElementById("sch-templates").value,
      cron: document.getElementById("sch-cron").value})});
  document.getElementById("sch-name").value = "";
  document.getElementById("sch-target").value = "";
  loadSchedules();
}

async function toggleSchedule(id) {
  await fetch("/api/schedules/"+id+"/toggle", {method:"POST"});
  loadSchedules();
}

async function deleteSchedule(id) {
  if (!confirm("確定刪除此排程？")) return;
  await fetch("/api/schedules/"+id, {method:"DELETE"});
  loadSchedules();
}

// ── Tools ─────────────────────────────────────────────
const TOOL_BADGE = {web:"tb-web",collab:"tb-collab",ad:"tb-ad",intel:"tb-intel",report:"tb-report",vuln:"tb-vuln",target:"tb-target"};

let toolsData = [], toolsFilter = "all";
let selectedTools = new Set(["nmap","nuclei","defectdojo","report"]);
let currentDetailId = null;

const TOOL_LABEL = {
  nmap:"Nmap", nuclei:"Nuclei", zap:"ZAP", sqlmap:"SQLMap",
  gobuster:"Gobuster", nikto:"Nikto", sliver:"Sliver C2",
  metasploit:"Metasploit", bloodhound:"BloodHound",
  defectdojo:"DefectDojo", report:"AI 報告",
  "kali-recon":"Kali Recon", "kali-exploit":"Kali Exploit",
  "kali-privesc":"Kali PrivEsc", "kali-post":"Kali Post",
  "scb-nmap":"SCB Nmap", "scb-nuclei":"SCB Nuclei",
  "scb-zap":"SCB ZAP", "scb-trivy":"SCB Trivy", "scb-semgrep":"SCB Semgrep",
};

async function loadPresets() {
  const grid = document.getElementById("preset-grid");
  if (!grid) return;
  try {
    const resp = await fetch("/api/presets");
    const presets = await resp.json();
    grid.innerHTML = presets.map(p => {
      const toolTags = p.tools.map(t =>
        `<span class="preset-tool-tag">${TOOL_LABEL[t]||t}</span>`
      ).join("");
      const phaseStr = p.phases.join(" → ");
      return `<div class="preset-card" id="preset-${p.id}" style="border-top:3px solid ${p.color};background:${p.bg}" onclick="applyPreset('${p.id}')">
<div class="preset-title" style="color:${p.color}">${p.name}</div>
<div class="preset-desc">${p.desc}</div>
<div class="preset-tools">${toolTags}</div>
<div class="preset-phases">${phaseStr}</div>
<button class="preset-action" style="background:${p.color};color:#fff">套用此套組 →</button>
</div>`;
    }).join("");
  } catch(e) {
    grid.innerHTML = '<div class="empty" style="grid-column:1/-1">載入失敗</div>';
  }
}

function applyPreset(id) {
  fetch("/api/presets").then(r=>r.json()).then(presets => {
    const p = presets.find(x => x.id === id);
    if (!p) return;
    selectedTools = new Set(p.tools);
    activePipelineTools = [...p.tools];
    document.querySelectorAll(".preset-card").forEach(c => c.classList.remove("active-preset"));
    const card = document.getElementById("preset-"+id);
    if (card) card.classList.add("active-preset");
    const picker = document.getElementById("tool-picker");
    if (picker) picker.querySelectorAll("input[type=checkbox]").forEach(cb => {
      cb.checked = selectedTools.has(cb.value);
    });
    updatePipeline();
    renderTools();
    updateToolsPipelinePreview();
    showPresetRunModal(p);
  });
}

function selectTargetMachine(btn, url, name) {
  document.getElementById("modal-target").value = url;
  if (!document.getElementById("modal-name").value)
    document.getElementById("modal-name").value = name;
  document.querySelectorAll("#target-machine-btns button").forEach(b => {
    b.style.borderColor = "#334155";
    b.style.color = "#94a3b8";
    b.style.background = "#0f172a";
  });
  btn.style.borderColor = "#3b82f6";
  btn.style.color = "#93c5fd";
  btn.style.background = "rgba(59,130,246,.15)";
}

function clearTargetMachineSelect() {
  document.getElementById("modal-target").value = "";
  document.getElementById("modal-target").focus();
  document.querySelectorAll("#target-machine-btns button").forEach(b => {
    b.style.borderColor = "#334155";
    b.style.color = "#94a3b8";
    b.style.background = "#0f172a";
  });
  const customBtn = document.getElementById("btn-custom-target");
  customBtn.style.borderColor = "#3b82f6";
  customBtn.style.color = "#93c5fd";
}

function showPresetRunModal(p) {
  let modal = document.getElementById("preset-modal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "preset-modal";
    modal.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:9999;display:flex;align-items:center;justify-content:center";
    modal.innerHTML = `<div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:1.75rem;width:480px;max-width:90vw">
<div style="font-size:1rem;font-weight:700;color:#f1f5f9;margin-bottom:.35rem" id="modal-title"></div>
<div style="font-size:.78rem;color:#64748b;margin-bottom:1.2rem" id="modal-desc"></div>
<div style="display:flex;flex-direction:column;gap:.75rem">
  <div>
    <label style="font-size:.75rem;color:#94a3b8;display:block;margin-bottom:.3rem">掃描目標</label>
    <div style="display:flex;gap:.5rem;margin-bottom:.4rem;flex-wrap:wrap" id="target-machine-btns">
      <span style="font-size:.72rem;color:#475569;align-self:center">靶機快選：</span>
      <button type="button" onclick="selectTargetMachine(this,'http://localhost:8888','crAPI 靶機掃描')"
        style="font-size:.72rem;padding:.25rem .6rem;border-radius:5px;border:1px solid #334155;background:#0f172a;color:#94a3b8;cursor:pointer">🎯 crAPI :8888</button>
      <button type="button" onclick="selectTargetMachine(this,'http://localhost:8080','DVWA 掃描')"
        style="font-size:.72rem;padding:.25rem .6rem;border-radius:5px;border:1px solid #334155;background:#0f172a;color:#94a3b8;cursor:pointer">🌐 DVWA :8080</button>
      <button type="button" onclick="selectTargetMachine(this,'http://localhost:8025','MailHog 掃描')"
        style="font-size:.72rem;padding:.25rem .6rem;border-radius:5px;border:1px solid #334155;background:#0f172a;color:#94a3b8;cursor:pointer">📧 MailHog :8025</button>
      <button type="button" id="btn-custom-target" onclick="clearTargetMachineSelect()"
        style="font-size:.72rem;padding:.25rem .6rem;border-radius:5px;border:1px solid #475569;background:transparent;color:#64748b;cursor:pointer">自訂</button>
    </div>
    <input id="modal-target" type="url" placeholder="https://target.example.com"
      style="width:100%;padding:.55rem .75rem;background:#0f172a;border:1px solid #334155;border-radius:7px;color:#f1f5f9;font-size:.85rem;outline:none;box-sizing:border-box" /></div>
  <div><label style="font-size:.75rem;color:#94a3b8;display:block;margin-bottom:.3rem">專案名稱</label>
    <input id="modal-name" placeholder="例：crAPI 靶機測試"
      style="width:100%;padding:.55rem .75rem;background:#0f172a;border:1px solid #334155;border-radius:7px;color:#f1f5f9;font-size:.85rem;outline:none;box-sizing:border-box" /></div>
  <label style="display:flex;align-items:center;gap:.5rem;font-size:.8rem;color:#94a3b8;cursor:pointer">
    <input type="checkbox" id="modal-report" checked style="accent-color:#3b82f6"> 執行完成後自動生成 AI 報告</label>
</div>
<div id="modal-pipeline" style="margin-top:1rem;display:flex;flex-wrap:wrap;gap:.3rem;align-items:center"></div>
<div style="display:flex;gap:.6rem;margin-top:1.25rem">
  <button id="modal-run-btn" style="flex:1;padding:.55rem;border-radius:7px;border:none;font-weight:700;font-size:.85rem;cursor:pointer;color:#fff" onclick="runPresetFromModal()">🚀 開始執行</button>
  <button style="padding:.55rem 1rem;border-radius:7px;border:1px solid #334155;background:transparent;color:#94a3b8;cursor:pointer;font-size:.85rem" onclick="document.getElementById('preset-modal').remove()">取消</button>
</div>
</div>`;
    document.body.appendChild(modal);
  }
  modal.style.display = "flex";
  document.getElementById("modal-title").textContent = p.name;
  document.getElementById("modal-desc").textContent = p.desc;
  const btn = document.getElementById("modal-run-btn");
  btn.style.background = p.color || "#3b82f6";
  btn.dataset.presetId = p.id;
  const pip = document.getElementById("modal-pipeline");
  pip.innerHTML = p.tools.map((t,i) =>
    `<span style="font-size:.7rem;padding:.15rem .4rem;border-radius:4px;background:#0f172a;border:1px solid #334155;color:#94a3b8">${TOOL_LABEL[t]||t}</span>`
    + (i < p.tools.length-1 ? '<span style="color:#475569;font-size:.7rem">→</span>' : "")
  ).join("");
  const savedTarget = document.getElementById("target")?.value;
  const savedName = document.getElementById("name")?.value;
  if (savedTarget && savedTarget !== "https://") document.getElementById("modal-target").value = savedTarget;
  if (savedName) document.getElementById("modal-name").value = savedName;
}

async function runPresetFromModal() {
  const btn = document.getElementById("modal-run-btn");
  const presetId = btn.dataset.presetId;
  const target = document.getElementById("modal-target").value.trim();
  const name = document.getElementById("modal-name").value.trim();
  const withReport = document.getElementById("modal-report").checked;
  if (!target || !name) { showNotice("請填寫目標 URL 和專案名稱"); return; }

  btn.textContent = "執行中..."; btn.disabled = true;

  try {
    const resp = await fetch(`/api/preset/${presetId}/run`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({target, name, with_report: withReport})
    });
    const data = await resp.json();
    if (data.error) { showNotice("錯誤："+data.error); btn.textContent="🚀 開始執行"; btn.disabled=false; return; }

    document.getElementById("preset-modal").remove();

    // 同步到掃描頁面的 target/name 欄位
    const tEl = document.getElementById("target");
    const nEl = document.getElementById("name");
    if (tEl) tEl.value = target;
    if (nEl) nEl.value = name;

    // 切換到掃描頁面監控進度
    switchTab("scan");
    document.getElementById("scan-btn").disabled = true;
    document.getElementById("stop-btn").style.display = "inline-block";
    document.getElementById("log-box").textContent = "套組任務已送出，Job ID: "+data.job_id+"\\n等待執行...";
    const badge = document.getElementById("status-badge");
    badge.className = "badge badge-running"; badge.textContent = "執行中";
    resetPipeline();
    if (activePipelineTools.length) setCurrentTool(activePipelineTools[0]);

    currentJobId = data.job_id;
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(() => pollStatus(), 2000);
    showNotice("✓ 套組「"+presetId+"」已開始執行");

  } catch(e) {
    showNotice("執行失敗："+e.message);
    btn.textContent = "🚀 開始執行"; btn.disabled = false;
  }
}

async function loadTools() {
  const grid = document.getElementById("tools-grid");
  grid.innerHTML = '<div class="empty" style="grid-column:1/-1">載入中...</div>';
  try { const resp = await fetch("/api/tools"); toolsData = await resp.json(); }
  catch(e) { toolsData = []; }
  renderTools();
  updateToolsPipelinePreview();
  loadPresets();
}

function filterTools(cat, btn) {
  toolsFilter = cat;
  document.querySelectorAll("#tools-filter-bar .filter-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  renderTools();
}

function renderTools() {
  const grid = document.getElementById("tools-grid");
  const data = toolsFilter==="all" ? toolsData
    : toolsFilter==="kali" ? toolsData.filter(t=>t.kali)
    : toolsFilter==="scb"  ? toolsData.filter(t=>t.scb)
    : toolsData.filter(t=>t.category===toolsFilter);
  if (!data.length) { grid.innerHTML = '<div class="empty" style="grid-column:1/-1">此分類無工具</div>'; return; }
  grid.innerHTML = data.map(t => {
    const isSel = selectedTools.has(t.id);
    const bc = TOOL_BADGE[t.category]||"tb-collab";
    const kT = t.kali ? '<span class="tool-badge" style="background:rgba(239,68,68,.1);color:#fca5a5">🐉 Kali</span>' : "";
    const sT = t.scb  ? '<span class="tool-badge" style="background:rgba(99,102,241,.12);color:#a5b4fc">⚙️ SCB</span>' : "";
    const bdr = t.kali ? "tool-cat-kali" : t.scb ? "tool-cat-scb" : "";
    const tid = t.id;
    return `<div class="tool-card ${isSel?"selected ":""}${bdr}" id="tc-${tid}" onclick="toggleToolSelectById('${tid}')" style="cursor:pointer">
<div class="tool-header"><div class="tool-name"><span class="running-dot ${t.running?"on":"off"}"></span>${t.name}</div>
<div style="display:flex;gap:.3rem;flex-wrap:wrap"><span class="tool-badge ${bc}">${t.category}</span>${kT}${sT}</div></div>
<div class="tool-desc">${t.desc}</div>
<div style="font-size:.72rem;color:var(--muted);margin-bottom:.5rem">${t.port?"Port "+t.port:"內建"}</div>
<div class="tool-actions" onclick="event.stopPropagation()">
${t.running?`<button class="btn-tool-stop" onclick="toolAction('${tid}','stop')">停止</button>`
          :`<button class="btn-tool-start" onclick="toolAction('${tid}','start')">啟動</button>`}
${t.url?`<a class="btn-tool-open" href="${t.url}" target="_blank" onclick="event.stopPropagation()">開啟 →</a>`:""}
<button class="btn-tool-open" style="background:transparent;border-color:var(--border)" onclick="event.stopPropagation();showToolDetail('${tid}')">詳情</button>
</div></div>`;
  }).join("");
  updateSelectedCount();
}

function toggleToolSelectById(id) {
  if (selectedTools.has(id)) selectedTools.delete(id);
  else selectedTools.add(id);
  const card = document.getElementById("tc-"+id);
  if (card) card.classList.toggle("selected", selectedTools.has(id));
  updateSelectedCount();
  updateToolsPipelinePreview();
}

function updateSelectedCount() {
  const el = document.getElementById("tools-selected-count");
  if (el) el.textContent = "已選 "+selectedTools.size+" 個工具";
}

function updateToolsPipelinePreview() {
  const preview = document.getElementById("tools-preview-pipeline");
  if (!preview) return;
  if (selectedTools.size === 0) { preview.innerHTML = '<div class="empty" style="padding:.5rem">尚未選擇工具</div>'; return; }
  const sel = [...selectedTools];
  preview.innerHTML = sel.map((id,i) => {
    const label = TOOL_LABEL[id] || id;
    const arrow = i < sel.length-1 ? '<div class="pipe-arrow done">→</div>' : "";
    return '<div class="pipe-node done">'+label+'</div>'+arrow;
  }).join("");
}

function clearToolSelection() {
  selectedTools.clear();
  document.querySelectorAll(".tool-card.selected").forEach(c=>c.classList.remove("selected"));
  updateSelectedCount(); updateToolsPipelinePreview();
}

function applyToolsToScan() {
  if (selectedTools.size===0) { showNotice("請先選取至少一個工具"); return; }
  activePipelineTools = [...selectedTools];
  const picker = document.getElementById("tool-picker");
  if (picker) picker.querySelectorAll("input[type=checkbox]").forEach(cb => { cb.checked = selectedTools.has(cb.value); });
  updatePipeline();
  switchTab("scan");
  showNotice("✓ 已套用 "+selectedTools.size+" 個工具到 Pipeline");
}

function showToolDetail(id) {
  currentDetailId = id;
  const t = toolsData.find(x=>x.id===id);
  if (!t) return;
  const card = document.getElementById("tool-detail-card");
  card.style.display = "block";
  document.getElementById("td-name").textContent = t.name;
  document.getElementById("td-desc").textContent = t.desc;
  document.getElementById("td-detail").textContent = t.detail||"";
  const sb = document.getElementById("td-select-btn");
  if (sb) {
    const isSel = selectedTools.has(id);
    sb.textContent = isSel ? "取消選取" : "加入工具組合";
    sb.className = (isSel ? "btn-secondary" : "btn-primary");
    sb.style.fontSize=".78rem"; sb.style.padding=".32rem .9rem";
  }
  document.getElementById("td-scb-badge").style.display = t.scb ? "block":"none";
  document.getElementById("td-kali-badge").style.display = t.kali? "block":"none";
  const cw = document.getElementById("td-cmds-wrap");
  if (t.cmds && t.cmds.length) {
    cw.style.display="block";
    document.getElementById("td-cmds").innerHTML = t.cmds.map(c =>
      `<div style="background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:.45rem .7rem;font-family:monospace;font-size:.76rem;color:#a3e635;display:flex;justify-content:space-between;align-items:center;gap:.5rem">
<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${c}</span>
<button onclick="navigator.clipboard.writeText(this.previousElementSibling.textContent);showNotice('已複製')" style="background:none;border:none;color:var(--muted);cursor:pointer;font-size:.7rem;flex-shrink:0">複製</button>
</div>`
    ).join("");
  } else { cw.style.display="none"; }
  const acts = document.getElementById("td-actions");
  acts.innerHTML = "";
  if (t.url) acts.innerHTML += `<a class="btn-tool-open" href="${t.url}" target="_blank" style="text-decoration:none">開啟 UI →</a>`;
  if (t.docs) acts.innerHTML += `<a class="btn-tool-open" href="${t.docs}" target="_blank" style="text-decoration:none;background:transparent;border-color:var(--border);color:var(--muted)">文件 ↗</a>`;
  acts.innerHTML += t.running
    ? `<button class="btn-tool-stop" onclick="toolAction('${id}','stop')">停止服務</button>`
    : `<button class="btn-tool-start" onclick="toolAction('${id}','start')">啟動服務</button>`;
  card.scrollIntoView({behavior:"smooth",block:"nearest"});
}

function toggleToolSelect() {
  if (currentDetailId) { toggleToolSelectById(currentDetailId); showToolDetail(currentDetailId); }
}

async function toolAction(id, action) {
  const resp = await fetch("/api/tool/"+id+"/"+action, {method:"POST"});
  const data = await resp.json();
  showNotice(data.msg||data.error||"操作完成");
  setTimeout(loadTools, 2000);
}

// ── Reports ───────────────────────────────────────────
const SEV_COLOR = {Critical:"#fda4af",High:"#fca5a5",Medium:"#fde68a",Low:"#93c5fd",Informational:"#94a3b8"};
const SEV_BG    = {Critical:"#4c0519",High:"#7f1d1d",Medium:"#78350f",Low:"#1e3a5f",Informational:"#1e293b"};

function _reportRow(f) {
  const enc = encodeURIComponent(f.name);
  const isArchived = f.archived;
  const bg = isArchived ? "rgba(30,41,59,.6)" : "var(--surface2)";
  const border = isArchived ? "1px dashed #334155" : "1px solid var(--border)";
  const archiveBtn = isArchived
    ? `<button onclick="reportAction('unarchive','${enc}')" title="還原" style="padding:.3rem .65rem;border-radius:6px;border:none;background:#1e3a5f;color:#93c5fd;font-size:.76rem;cursor:pointer">↩ 還原</button>`
    : `<button onclick="reportAction('archive','${enc}')" title="歸檔" style="padding:.3rem .65rem;border-radius:6px;border:none;background:#1e293b;color:#94a3b8;font-size:.76rem;cursor:pointer">📁 歸檔</button>`;
  return `
<div id="rrow-${enc}" style="display:flex;justify-content:space-between;align-items:center;padding:.7rem 1rem;background:${bg};border:${border};border-radius:8px;gap:.5rem">
  <input type="checkbox" class="report-cb" data-name="${f.name}" data-archived="${isArchived}"
    onclick="updateBulkBar()"
    style="width:15px;height:15px;flex-shrink:0;accent-color:#6366f1;cursor:pointer">
  <div style="flex:1;min-width:0">
    <div style="font-size:.84rem;font-weight:600;color:${isArchived?"#94a3b8":"#f1f5f9"};white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${isArchived?"<span style='font-size:.7rem;background:#334155;color:#94a3b8;padding:.1rem .4rem;border-radius:4px;margin-right:.4rem'>已歸檔</span>":""}${f.name}</div>
    <div style="font-size:.71rem;color:var(--muted);margin-top:.15rem">${f.mtime} ｜ ${(f.size/1024).toFixed(1)} KB</div>
  </div>
  <div style="display:flex;gap:.4rem;flex-shrink:0">
    <a href="${f.url}" download="${f.name}" style="padding:.3rem .7rem;background:#1d4ed8;color:#fff;border-radius:6px;font-size:.76rem;font-weight:600;text-decoration:none;white-space:nowrap">⬇ 下載</a>
    ${archiveBtn}
    <button onclick="reportAction('delete','${enc}')" title="刪除" style="padding:.3rem .65rem;border-radius:6px;border:none;background:#450a0a;color:#fca5a5;font-size:.76rem;cursor:pointer">🗑</button>
  </div>
</div>`;
}

function updateBulkBar() {
  const cbs = document.querySelectorAll(".report-cb");
  const checked = document.querySelectorAll(".report-cb:checked");
  const bar = document.getElementById("bulk-action-bar");
  const countEl = document.getElementById("bulk-count");
  const selectAllCb = document.getElementById("select-all-cb");
  if (bar) bar.style.display = checked.length ? "flex" : "none";
  if (countEl) countEl.textContent = `已選 ${checked.length} 份`;
  if (selectAllCb) selectAllCb.indeterminate = checked.length > 0 && checked.length < cbs.length;
  if (selectAllCb) selectAllCb.checked = checked.length === cbs.length && cbs.length > 0;
}

function toggleSelectAll(cb) {
  document.querySelectorAll(".report-cb").forEach(c => { c.checked = cb.checked; });
  updateBulkBar();
}

async function bulkAction(action) {
  const checked = [...document.querySelectorAll(".report-cb:checked")];
  if (!checked.length) return;
  if (action === "delete" && !confirm(`確定刪除選取的 ${checked.length} 份報告？此操作無法復原。`)) return;
  const names = checked.map(c => c.dataset.name);
  const method = action === "delete" ? "DELETE" : "POST";
  await Promise.all(names.map(name =>
    fetch(`/api/reports/${action}/${encodeURIComponent(name)}`, {method}).catch(() => {})
  ));
  await loadAiReports();
  showNotice(`已完成：${action === "delete" ? "刪除" : action === "archive" ? "歸檔" : "還原"} ${names.length} 份報告`);
}

async function reportAction(action, encodedName) {
  const name = decodeURIComponent(encodedName);
  if (action === "delete" && !confirm(`確定刪除「${name}」？此操作無法復原。`)) return;
  const method = action === "delete" ? "DELETE" : "POST";
  const url = `/api/reports/${action}/${encodedName}`;
  try {
    const r = await fetch(url, {method});
    const d = await r.json();
    if (d.ok) loadAiReports();
    else showNotice("操作失敗：" + (d.error || "未知錯誤"), true);
  } catch(e) {
    showNotice("請求失敗：" + e.message, true);
  }
}

async function loadAiReports() {
  const container = document.getElementById("ai-reports-list");
  if (!container) return;
  container.innerHTML = '<div class="empty">載入中...</div>';
  try {
    const resp = await fetch("/api/reports/list");
    const data = await resp.json();
    const active   = data.filter(f => !f.archived);
    const archived = data.filter(f =>  f.archived);

    if (!data.length) {
      container.innerHTML = '<div class="empty">尚無 AI 報告 — 執行套組掃描後自動生成，或在下方手動指定 Engagement 生成</div>';
      return;
    }

    let html = '<div style="display:grid;gap:.4rem">';
    html += `<div id="bulk-action-bar" style="display:none;align-items:center;gap:.5rem;padding:.5rem .75rem;background:#1e293b;border:1px solid #334155;border-radius:8px;margin-bottom:.25rem">
      <span id="bulk-count" style="font-size:.78rem;color:#93c5fd;margin-right:.25rem"></span>
      <button onclick="bulkAction('archive')" style="padding:.28rem .7rem;background:#1e3a5f;color:#93c5fd;border:none;border-radius:5px;font-size:.75rem;cursor:pointer">📁 批次歸檔</button>
      <button onclick="bulkAction('unarchive')" style="padding:.28rem .7rem;background:#1e293b;color:#94a3b8;border:1px solid #334155;border-radius:5px;font-size:.75rem;cursor:pointer">↩ 批次還原</button>
      <button onclick="bulkAction('delete')" style="padding:.28rem .7rem;background:#450a0a;color:#fca5a5;border:none;border-radius:5px;font-size:.75rem;cursor:pointer">🗑 批次刪除</button>
    </div>`;
    html += `<div style="display:flex;align-items:center;gap:.5rem;padding:.3rem .25rem;margin-bottom:.1rem">
      <input type="checkbox" id="select-all-cb" onclick="toggleSelectAll(this)"
        style="width:15px;height:15px;accent-color:#6366f1;cursor:pointer">
      <span style="font-size:.75rem;color:var(--muted)">全選</span>
    </div>`;
    if (active.length) {
      html += active.map(_reportRow).join("");
    } else {
      html += '<div class="empty" style="padding:.5rem 0">所有報告已歸檔</div>';
    }
    if (archived.length) {
      html += `<div style="margin-top:.75rem;padding-top:.75rem;border-top:1px solid #1e293b">
        <div style="font-size:.72rem;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.4rem">📁 已歸檔（${archived.length}）</div>`
        + archived.map(_reportRow).join("") + "</div>";
    }
    html += '</div>';
    container.innerHTML = html;
  } catch(e) {
    container.innerHTML = '<div class="empty">載入失敗：'+e.message+'</div>';
  }
}

async function generateAiReport() {
  const engId  = document.getElementById("gen-eng-id").value.trim();
  const name   = document.getElementById("gen-report-name").value.trim() || "report";
  const target = document.getElementById("gen-target").value.trim();
  const tools  = document.getElementById("gen-tools").value.trim();
  const status = document.getElementById("gen-status");
  const btn    = document.getElementById("gen-btn");
  if (!engId) { status.textContent = "請填寫 Engagement ID"; status.style.color="#fca5a5"; return; }

  btn.disabled = true; btn.textContent = "生成中...";
  status.style.color = "#93c5fd";
  status.textContent = "AI 報告生成中，Ollama 需要 5-10 分鐘，完成後自動出現在上方列表...";

  try {
    const resp = await fetch("/api/reports/generate", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({engagement_id: parseInt(engId), name, target, tools})
    });
    const data = await resp.json();
    if (data.error) {
      status.textContent = "錯誤：" + data.error;
      status.style.color = "#fca5a5";
      btn.disabled = false; btn.textContent = "🚀 生成報告";
      return;
    }
    const jobId = data.job_id;
    const poll = setInterval(async () => {
      try {
        const sr = await fetch("/api/status/" + jobId);
        const sd = await sr.json();
        const last = (sd.logs || []).slice(-1)[0] || "";
        status.textContent = last;
        if (sd.status === "done") {
          clearInterval(poll);
          status.style.color = "#86efac";
          btn.disabled = false; btn.textContent = "🚀 生成報告";
          loadAiReports();
          showNotice("✓ AI 報告生成完成");
        } else if (sd.status === "failed") {
          clearInterval(poll);
          status.style.color = "#fca5a5";
          btn.disabled = false; btn.textContent = "🚀 生成報告";
        }
      } catch(e) { clearInterval(poll); }
    }, 3000);
  } catch(e) {
    status.textContent = "請求失敗：" + e.message;
    status.style.color = "#fca5a5";
    btn.disabled = false; btn.textContent = "🚀 生成報告";
  }
}

async function loadReports() {
  const container = document.getElementById("reports-list");
  container.innerHTML = '<div class="empty">載入中...</div>';
  const resp = await fetch("/api/reports");
  const data = await resp.json();
  if (data.error) { container.innerHTML = '<div class="empty">無法連線 DefectDojo：'+data.error+'</div>'; return; }
  if (!data.length) { container.innerHTML = '<div class="empty">尚無 Engagement</div>'; return; }
  container.innerHTML = data.map(e => {
    const sevTags = Object.entries(e.severity)
      .filter(([,v]) => v > 0)
      .map(([k,v]) => '<span class="rs-tag" style="background:'+SEV_BG[k]+';color:'+SEV_COLOR[k]+'">'+k[0]+':'+v+'</span>')
      .join("");
    return '<div class="report-item">'
      + '<div class="report-header">'
      + '<div><div class="report-name">'+e.name+'</div>'
      + '<div class="report-meta">Engagement #'+e.id+' ｜ 狀態：'+e.status+' ｜ Findings：'+e.findings_count+'</div>'
      + '<div class="report-sev">'+sevTags+'</div></div>'
      + '<div style="display:flex;gap:.5rem">'
      + `<button class="btn-report-view" onclick="viewReport(${e.id},'${e.name.replace(/'/g,"\\'")}')">查看報表</button>`
      + `<button style="padding:.32rem .75rem;border-radius:6px;border:none;background:#1d4ed8;color:#fff;font-size:.75rem;cursor:pointer" onclick="document.getElementById('gen-eng-id').value=${e.id};document.getElementById('gen-report-name').value='${e.name.replace(/'/g,"\\'")}';document.querySelector('#tab-reports .card:nth-child(2)').scrollIntoView({behavior:'smooth'})">🤖 AI 報告</button>`
      + '</div>'
      + '</div></div>';
  }).join("");
}

function viewReport(eid, name) {
  window.open("/api/reports/"+eid+"/html", "_blank");
}

// ── Hub ───────────────────────────────────────────────
let hubData = [];

async function loadHub() {
  const wrap = document.getElementById("hub-table-wrap");
  const summary = document.getElementById("hub-summary");
  wrap.innerHTML = '<div class="empty">載入中...</div>';
  const resp = await fetch("/api/containers");
  const data = await resp.json();
  if (data.error) { wrap.innerHTML = '<div class="empty">無法取得容器資料：'+data.error+'</div>'; return; }
  hubData = data;
  const running = data.filter(c => c.state === "running").length;
  const exited  = data.filter(c => c.state === "exited").length;
  summary.innerHTML =
    '<span class="hub-sum-item" style="color:#86efac">▶ 運行中 '+running+'</span>' +
    '<span class="hub-sum-item" style="color:#f87171">■ 已停止 '+exited+'</span>' +
    '<span class="hub-sum-item" style="color:#94a3b8">總計 '+data.length+'</span>';
  renderHub(data);
}

function renderHub(data) {
  const wrap = document.getElementById("hub-table-wrap");
  if (!data.length) { wrap.innerHTML = '<div class="empty">無容器</div>'; return; }
  let html = '<table class="hub-table"><thead><tr>'
    + '<th>名稱</th><th>Image</th><th>狀態</th><th>Ports</th><th>操作</th>'
    + '</tr></thead><tbody>';
  for (const c of data) {
    const stateClass = c.state === "running" ? "state-running" : c.state === "paused" ? "state-paused" : "state-exited";
    const ports = c.ports ? c.ports.replace(/0[.]0[.]0[.]0:/g,"").replace(/:::/g,"") : "-";
    const actions = c.state === "running"
      ? `<button class="btn-hub btn-hub-stop" onclick="hubAction('${c.id}','stop')">停止</button>`
        + `<button class="btn-hub btn-hub-restart" onclick="hubAction('${c.id}','restart')">重啟</button>`
      : `<button class="btn-hub btn-hub-start" onclick="hubAction('${c.id}','start')">啟動</button>`;
    html += '<tr>'
      + '<td style="font-family:monospace;font-size:.8rem;color:#93c5fd">'+c.name+'</td>'
      + '<td style="color:#64748b;font-size:.78rem;max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="'+c.image+'">'+c.image+'</td>'
      + '<td><span class="'+stateClass+'">'+c.status+'</span></td>'
      + '<td style="font-size:.75rem;color:#475569">'+ports+'</td>'
      + '<td><div class="hub-actions">'+actions+'</div></td>'
      + '</tr>';
  }
  html += '</tbody></table>';
  wrap.innerHTML = html;
}

function filterHub() {
  const q = document.getElementById("hub-search").value.toLowerCase();
  renderHub(hubData.filter(c => c.name.toLowerCase().includes(q) || c.image.toLowerCase().includes(q)));
}

async function hubAction(id, action) {
  const resp = await fetch("/api/containers/"+id+"/"+action, {method:"POST"});
  const data = await resp.json();
  const notice = document.createElement("div");
  notice.style.cssText = "position:fixed;bottom:1.5rem;right:1.5rem;background:#1e293b;border:1px solid #334155;color:#e2e8f0;padding:.75rem 1.25rem;border-radius:8px;font-size:.85rem;z-index:999";
  notice.textContent = data.ok ? (data.out || "操作成功") : ("失敗：" + (data.error||data.out||"未知錯誤"));
  document.body.appendChild(notice);
  setTimeout(() => notice.remove(), 3000);
  setTimeout(loadHub, 2500);
}

// ── Image 倉庫 ────────────────────────────────────────
let imagesPullJobId = null, imagesPollTimer = null;

const CAT_COLOR = {scan:"#3b82f6",dast:"#f97316",exploit:"#ef4444",recon:"#8b5cf6"};
const CAT_LABEL = {scan:"掃描",dast:"DAST",exploit:"注入",recon:"路徑枚舉"};

async function loadImages() {
  const container = document.getElementById("images-list");
  if (!container) return;
  container.innerHTML = '<div class="empty">查詢本機 image 狀態...</div>';
  try {
    const resp = await fetch("/api/images");
    const data = await resp.json();
    if (!data.length) { container.innerHTML = '<div class="empty">無 image 資料</div>'; return; }

    let html = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem">';
    for (const img of data) {
      const present = img.present;
      const statusDot = present
        ? '<span style="width:7px;height:7px;border-radius:50%;background:#22c55e;box-shadow:0 0 5px rgba(34,197,94,.5);display:inline-block;margin-right:.4rem"></span>'
        : '<span style="width:7px;height:7px;border-radius:50%;background:#ef4444;display:inline-block;margin-right:.4rem"></span>';
      const statusLabel = present
        ? `<span style="color:#86efac;font-size:.72rem">${img.size_mb} MB · ${img.created}</span>`
        : '<span style="color:#f87171;font-size:.72rem">未下載</span>';
      const catColor = CAT_COLOR[img.category] || "#64748b";
      const catLabel = CAT_LABEL[img.category] || img.category;
      html += `
<div style="background:var(--surface2);border:1px solid var(--border);border-radius:10px;padding:1rem;display:flex;flex-direction:column;gap:.5rem">
  <div style="display:flex;justify-content:space-between;align-items:flex-start">
    <div style="font-size:.88rem;font-weight:700;color:#f1f5f9">${statusDot}${img.name}</div>
    <span style="font-size:.62rem;padding:.1rem .42rem;border-radius:4px;font-weight:700;background:${catColor}22;color:${catColor};border:1px solid ${catColor}44">${catLabel}</span>
  </div>
  <div style="font-family:monospace;font-size:.72rem;color:#64748b">${img.image}:<span style="color:#93c5fd">${img.tag}</span></div>
  <div style="font-size:.72rem;color:var(--muted)">${img.desc}</div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-top:.25rem">
    ${statusLabel}
    <button onclick="pullImage('${img.id}','${img.image}:${img.tag}')"
      style="padding:.28rem .75rem;border-radius:6px;border:none;background:${present?'#1e3a5f':'#1d4ed8'};color:${present?'#93c5fd':'#fff'};font-size:.73rem;font-weight:600;cursor:pointer">
      ${present ? '🔄 更新' : '⬇ 下載'}
    </button>
  </div>
  ${img.digest ? `<div style="font-family:monospace;font-size:.65rem;color:#334155">ID: ${img.digest}</div>` : ''}
</div>`;
    }
    html += '</div>';
    container.innerHTML = html;
  } catch(e) {
    container.innerHTML = '<div class="empty">載入失敗：' + e.message + '</div>';
  }
}

async function pullImage(imageId, fullName) {
  const log = document.getElementById("images-pull-log");
  log.style.display = "block";
  log.textContent = `開始 pull ${fullName}...\n`;
  const resp = await fetch(`/api/images/${imageId}/pull`, {method:"POST"});
  const data = await resp.json();
  if (data.error) { log.textContent += "錯誤：" + data.error; return; }
  startImagesPoll(data.job_id, log);
}

async function pullAllImages() {
  const log = document.getElementById("images-pull-log");
  const btn = document.getElementById("pull-all-btn");
  log.style.display = "block";
  log.textContent = "開始全部 pull...\n";
  btn.disabled = true; btn.textContent = "下載中...";
  const resp = await fetch("/api/images/pull-all", {method:"POST"});
  const data = await resp.json();
  if (data.error) { log.textContent += "錯誤：" + data.error; btn.disabled=false; btn.textContent="⬇ 全部更新"; return; }
  startImagesPoll(data.job_id, log, () => {
    btn.disabled = false; btn.textContent = "⬇ 全部更新";
    loadImages();
  });
}

function startImagesPoll(jobId, logEl, onDone) {
  if (imagesPollTimer) clearInterval(imagesPollTimer);
  imagesPollTimer = setInterval(async () => {
    try {
      const r = await fetch("/api/status/" + jobId);
      const d = await r.json();
      logEl.textContent = d.logs.join("\n");
      logEl.scrollTop = logEl.scrollHeight;
      if (d.status === "done" || d.status === "failed") {
        clearInterval(imagesPollTimer);
        if (onDone) onDone();
        else loadImages();
      }
    } catch(e) { clearInterval(imagesPollTimer); }
  }, 1500);
}

// ── showNotice shared ─────────────────────────────────
function showNotice(msg) {
  const n = document.createElement("div");
  n.style.cssText = "position:fixed;bottom:1.5rem;right:1.5rem;background:var(--surface);border:1px solid var(--border);color:var(--text);padding:.75rem 1.25rem;border-radius:9px;font-size:.83rem;z-index:999;box-shadow:0 4px 20px rgba(0,0,0,.4)";
  n.textContent = msg;
  document.body.appendChild(n);
  setTimeout(() => n.remove(), 3000);
}

// ── AI 攻擊劇本 ───────────────────────────────────────
async function runAI() {
  const btn = document.getElementById("ai-btn");
  btn.disabled = true; btn.textContent = "產出中...";
  const target = document.getElementById("ai-target").value;
  const scenario = document.getElementById("ai-scenario").value;
  const context = document.getElementById("ai-context").value;
  const card = document.getElementById("ai-result-card");
  const output = document.getElementById("ai-output");
  output.textContent = "⏳ Ollama 分析中，請稍候...";
  card.style.display = "block";
  try {
    const resp = await fetch("/api/ai/playbook", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({target, scenario, context})
    });
    const data = await resp.json();
    output.textContent = data.playbook || data.error || "無回應";
    document.getElementById("ai-actions").innerHTML =
      '<button class="btn-primary" style="font-size:.8rem;padding:.45rem 1.2rem" onclick="confirmExecute()">⚠️ 確認執行</button>' +
      '<button class="btn-secondary" style="margin-left:.5rem" onclick="exportPlaybook()">匯出劇本</button>';
  } catch(e) {
    output.textContent = "錯誤："+e.message+"\\n\\n（提示：請確認 Ollama 服務已在 localhost:11434 啟動）";
  }
  btn.disabled = false; btn.textContent = "產出攻擊劇本";
}

function copyAI() {
  navigator.clipboard.writeText(document.getElementById("ai-output").textContent);
  showNotice("已複製攻擊劇本");
}

function confirmExecute() {
  if (!confirm("⚠️ 警告：即將執行 AI 建議的攻擊操作。\\n請確認此為授權測試環境。確定繼續？")) return;
  showNotice("已送出執行指令 — 請至 C2 控制台查看進度");
}

function exportPlaybook() {
  const text = document.getElementById("ai-output").textContent;
  const blob = new Blob([text], {type:"text/plain"});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
  a.download = "attack-playbook-"+Date.now()+".txt"; a.click();
}

// ── C2 控制台 ─────────────────────────────────────────
const MOCK_SESSIONS = [
  {id:"a1b2c3d4",host:"DESKTOP-WIN10",ip:"192.168.1.55",os:"Windows 10",priv:"SYSTEM",heartbeat:"5s ago"},
  {id:"e5f6g7h8",host:"ubuntu-srv-01",ip:"10.0.0.12",os:"Linux",priv:"root",heartbeat:"12s ago"},
];

function loadC2() {
  document.getElementById("c2-sessions").textContent = MOCK_SESSIONS.length;
  document.getElementById("c2-implants").textContent = 3;
  document.getElementById("c2-listeners").textContent = 2;
  const badge = document.getElementById("c2-status-badge");
  badge.textContent = "連線中";
  badge.style.cssText += ";background:rgba(34,197,94,.12);color:#86efac;border-color:rgba(34,197,94,.25)";
  document.getElementById("c2-sessions-body").innerHTML = MOCK_SESSIONS.map(s =>
    '<tr>'
    +'<td style="font-family:monospace;color:#93c5fd;font-size:.78rem">'+s.id+'</td>'
    +'<td>'+s.host+'</td><td style="color:var(--muted)">'+s.ip+'</td>'
    +'<td style="color:var(--muted)">'+s.os+'</td>'
    +'<td><span class="sev-tag '+(s.priv==="SYSTEM"||s.priv==="root"?"sev-High":"sev-Low")+'">'+s.priv+'</span></td>'
    +'<td style="color:var(--muted);font-size:.76rem">'+s.heartbeat+'</td>'
    +'<td><div class="hub-actions">'
    +'<button class="btn-hub btn-hub-start" onclick="openShell("'+s.id+'")">Shell</button>'
    +'<button class="btn-hub btn-hub-restart" onclick="runLateral("'+s.id+'")">橫移</button>'
    +'<button class="btn-hub btn-hub-stop" onclick="killSession("'+s.id+'")">終止</button>'
    +'</div></td></tr>'
  ).join("");
}

function generateImplant() {
  const os = document.getElementById("implant-os").value;
  const lhost = document.getElementById("implant-lhost").value || "192.168.1.106";
  const proto = document.getElementById("implant-proto").value;
  const name = document.getElementById("implant-name").value || "agent";
  const ext = os.includes("Windows") ? ".exe" : "";
  const div = document.getElementById("implant-result");
  div.style.display = "block";
  div.innerHTML = '<div style="background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:.85rem;font-family:monospace;font-size:.78rem">'
    +'<div style="color:var(--muted);margin-bottom:.4rem">生成指令：</div>'
    +'<div style="color:#a3e635">sliver-server &gt; generate --'+proto.toLowerCase()+' '+lhost+' --os '+os.split(" ")[0].toLowerCase()+' --arch '+os.split(" ")[1]+' --name '+name+ext+'</div>'
    +'<div style="color:var(--muted);margin-top:.4rem;font-size:.72rem">協定：'+proto+' ｜ 回連：'+lhost+':443</div>'
    +'</div>';
  showNotice("Implant 配置已產生");
}

function openShell(id) { showNotice("Shell 連線："+id+" — 請至終端機執行 sliver-client"); }
function runLateral(id) { showNotice("橫向移動模組啟動："+id); }
function killSession(id) {
  if (!confirm("終止 Session "+id+"？")) return;
  showNotice("已終止 Session："+id);
  loadC2();
}

// ── AD 攻擊路徑 ───────────────────────────────────────
function runSharpHound() {
  const dc = document.getElementById("ad-dc").value;
  if (!dc) { alert("請輸入 Domain Controller IP"); return; }
  const log = document.getElementById("ad-collect-log");
  log.style.display = "block"; log.textContent = "";
  const msgs = [
    "初始化 SharpHound 收集器...",
    "連線至 DC: "+dc,
    "收集 Users... (1024 物件)",
    "收集 Computers... (256 物件)",
    "收集 Groups... (512 物件)",
    "收集 GPOs... (128 物件)",
    "收集 ACLs...",
    "壓縮輸出 → BloodHound_"+new Date().toISOString().slice(0,10).replace(/-/g,"")+".zip",
    "✓ 收集完成，請上傳至 BloodHound UI",
  ];
  let i = 0;
  const t = setInterval(() => {
    if (i >= msgs.length) { clearInterval(t); return; }
    log.textContent += "["+new Date().toLocaleTimeString()+"] "+msgs[i]+"\\n";
    log.scrollTop = log.scrollHeight; i++;
  }, 600);
}

function queryADPaths() {
  const paths = [
    {from:"john.smith@corp.local",  to:"Domain Admins",    hops:3, risk:"High",   via:"ACL Abuse → Kerberoasting → DCSync"},
    {from:"svc_backup@corp.local",  to:"Domain Admins",    hops:2, risk:"High",   via:"WriteDACL → AdminSDHolder"},
    {from:"helpdesk@corp.local",    to:"Enterprise Admins",hops:4, risk:"Medium", via:"RDP → LocalAdmin → DCSync"},
  ];
  document.getElementById("ad-da").textContent = paths.length;
  document.getElementById("ad-users").textContent = "1,024";
  document.getElementById("ad-computers").textContent = "256";
  document.getElementById("ad-groups").textContent = "512";
  document.getElementById("ad-paths").innerHTML = paths.map(p =>
    '<div style="background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:.85rem;margin-bottom:.45rem">'
    +'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.4rem">'
    +'<div style="font-size:.83rem;font-weight:600">'+p.from+' → <span style="color:#fca5a5">'+p.to+'</span></div>'
    +'<span class="sev-tag sev-'+p.risk+'">'+p.hops+' Hops</span></div>'
    +'<div style="font-size:.76rem;color:var(--muted);font-family:monospace">'+p.via+'</div>'
    +'<div style="margin-top:.5rem;display:flex;gap:.38rem">'
    +'<button class="btn-hub btn-hub-restart" onclick="showNotice("路徑詳情已載入")">詳情</button>'
    +'<button class="btn-hub btn-hub-start" onclick="showNotice("已加入攻擊計劃")">加入計劃</button>'
    +'</div></div>'
  ).join("");
}

// ── 事件流 ────────────────────────────────────────────
let evStream = null, evFilter = "all";
let evCounts = {total:0, alert:0, c2:0, scan:0};
const EV_COLORS = {alert:{label:"ALERT",color:"#fca5a5",bg:"rgba(239,68,68,.1)"},c2:{label:"C2",color:"#fde68a",bg:"rgba(234,179,8,.08)"},scan:{label:"SCAN",color:"#93c5fd",bg:"rgba(59,130,246,.08)"},info:{label:"INFO",color:"var(--muted)",bg:"rgba(30,41,59,.4)"}};
const MOCK_EVENTS = [
  {type:"scan",  msg:"Nuclei 掃描完成：crapi-exposure-v2 — 12 findings",       src:"secureCodeBox"},
  {type:"c2",    msg:"Sliver implant 回連：DESKTOP-WIN10 / 192.168.1.55",       src:"Sliver C2"},
  {type:"alert", msg:"高危漏洞：Laravel .env 暴露 — 192.168.1.106:8888",        src:"DefectDojo"},
  {type:"c2",    msg:"橫向移動嘗試：ubuntu-srv-01 → 10.0.0.12",                 src:"Sliver C2"},
  {type:"scan",  msg:"Nmap 資產盤點：發現 5 個開放埠",                           src:"secureCodeBox"},
  {type:"alert", msg:"告警：暴力破解嘗試 — ssh / 192.168.1.1",                   src:"Kafka"},
  {type:"info",  msg:"DefectDojo engagement 更新：crAPI K8s Pipeline",          src:"DefectDojo"},
];

function toggleEventStream() {
  const btn = document.querySelector("[onclick='toggleEventStream()']");
  if (evStream) {
    clearInterval(evStream); evStream = null;
    document.getElementById("kafka-dot").style.cssText = "width:8px;height:8px;border-radius:50%;background:var(--muted);display:inline-block";
    document.getElementById("kafka-status").textContent = "已中斷";
    btn.textContent = "連線";
  } else {
    document.getElementById("kafka-dot").style.cssText = "width:8px;height:8px;border-radius:50%;background:#22c55e;box-shadow:0 0 6px rgba(34,197,94,.5);display:inline-block";
    document.getElementById("kafka-status").textContent = "串流中";
    btn.textContent = "中斷";
    let idx = 0;
    evStream = setInterval(() => { addEvent(MOCK_EVENTS[idx++ % MOCK_EVENTS.length]); }, 2000);
  }
}

function addEvent(ev) {
  evCounts.total++;
  if (ev.type==="alert") evCounts.alert++;
  if (ev.type==="c2")    evCounts.c2++;
  if (ev.type==="scan")  evCounts.scan++;
  ["total","alert","c2","scan"].forEach(k => { const el=document.getElementById("ev-"+k); if(el) el.textContent=evCounts[k]; });
  if (evFilter!=="all" && ev.type!==evFilter) return;
  const t = EV_COLORS[ev.type] || EV_COLORS.info;
  const tl = document.getElementById("event-timeline");
  if (tl.querySelector(".empty")) tl.innerHTML = "";
  const div = document.createElement("div");
  div.style.cssText = "display:flex;gap:.6rem;align-items:flex-start;padding:.48rem .65rem;background:"+t.bg+";border-radius:6px;border:1px solid rgba(255,255,255,.04)";
  div.innerHTML = '<span style="font-size:.68rem;padding:.1rem .42rem;border-radius:4px;font-weight:700;color:'+t.color+';background:rgba(0,0,0,.25);white-space:nowrap;flex-shrink:0">'+t.label+'</span>'
    +'<span style="font-size:.78rem;color:#cbd5e1;flex:1">'+ev.msg+'</span>'
    +'<span style="font-size:.68rem;color:var(--muted);white-space:nowrap">'+new Date().toLocaleTimeString()+'</span>';
  tl.insertBefore(div, tl.firstChild);
  if (tl.children.length > 60) tl.removeChild(tl.lastChild);
}

function setEvFilter(f, btn) {
  evFilter = f;
  document.querySelectorAll("[onclick^='setEvFilter']").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
}

// ── 服務控制台 ────────────────────────────────────────────
let labPollTimer = null;

async function loadLabGroups() {
  try {
    const data = await fetch("/api/lab/groups").then(r => r.json());
    renderLabGroups(data);
  } catch(e) {
    console.error("loadLabGroups error:", e);
    const wrap = document.getElementById("lab-groups");
    if (wrap) wrap.innerHTML = `<div class="empty">載入失敗：${e.message}</div>`;
  }
}

function renderLabGroups(groups) {
  var wrap = document.getElementById("lab-groups");
  if (!wrap) return;
  if (!groups || !groups.length) { wrap.innerHTML = '<div class="empty">無服務群組</div>'; return; }
  var COLORS = {core:"#3b82f6",targets:"#f97316",redteam:"#ef4444",platform:"#8b5cf6",reporting:"#10b981",adrecon:"#6366f1"};
  wrap.innerHTML = "";
  for (var i = 0; i < groups.length; i++) {
    var g = groups[i];
    var isR = g.overall === "running";
    var isP = g.overall === "partial";
    var dot = isR ? "#22c55e" : isP ? "#f59e0b" : "#475569";
    var lbl = isR ? "運行中" : isP ? ("部分 "+g.running+"/"+g.total) : "已停止";
    var clr = COLORS[g.id] || "#64748b";
    var det = "";
    if (g.details) {
      for (var j = 0; j < g.details.length; j++) {
        var sc = g.details[j].state === "running" ? "#22c55e" : "#475569";
        det += '<span style="font-size:.68rem;color:'+sc+'">&#9679; '+g.details[j].service+'</span> ';
      }
    }
    var sBg  = isR ? "rgba(34,197,94,.1)"   : "rgba(59,130,246,.15)";
    var sClr = isR ? "#22c55e" : "#60a5fa";
    var sLbl = isR ? "&#10003; 運行中" : "&#9654; 啟動";
    var id   = g.id;
    var row  = '<div style="display:flex;align-items:center;gap:1rem;padding:.65rem .9rem;background:var(--card-bg);border-radius:8px;border:1px solid var(--border);margin-bottom:.4rem">'
      +'<div style="width:10px;height:34px;border-radius:3px;background:'+clr+';flex-shrink:0"></div>'
      +'<div style="flex:1;min-width:0">'
        +'<div style="display:flex;align-items:center;gap:.5rem">'
          +'<span style="font-weight:600;font-size:.85rem">'+g.name+'</span>'
          +'<span style="width:7px;height:7px;border-radius:50%;background:'+dot+';flex-shrink:0"></span>'
          +'<span style="font-size:.72rem;color:'+dot+'">'+lbl+'</span>'
        +'</div>'
        +'<div style="font-size:.72rem;color:var(--muted);margin:.15rem 0 .25rem">'+g.desc+'</div>'
        +'<div style="display:flex;flex-wrap:wrap;gap:.3rem">'+det+'</div>'
      +'</div>'
      +'<div style="display:flex;gap:.4rem;flex-shrink:0">'
        +'<button onclick="labGroupAction(\''+id+'\',\'start\')" style="padding:.28rem .7rem;border-radius:6px;border:none;background:'+sBg+';color:'+sClr+';font-size:.75rem;cursor:pointer">'+sLbl+'</button>'
        +'<button onclick="labGroupAction(\''+id+'\',\'stop\')" style="padding:.28rem .7rem;border-radius:6px;border:1px solid #ef4444;background:rgba(239,68,68,.08);color:#ef4444;font-size:.75rem;cursor:pointer">&#9632; 停止</button>'
      +'</div>'
    +'</div>';
    wrap.innerHTML += row;
  }
}
async function labGroupAction(groupId, action) {
  const logCard  = document.getElementById("lab-log-card");
  const logBox   = document.getElementById("lab-log");
  const logTitle = document.getElementById("lab-log-title");
  logCard.style.display = "block";
  logBox.innerHTML = "";
  logTitle.textContent = action === "start" ? "▶ 啟動服務" : "⏹ 停止服務";

  const resp = await fetch(`/api/lab/${groupId}/${action}`, {method:"POST"}).then(r=>r.json());
  if (!resp.job_id) { logBox.textContent = "啟動失敗"; return; }
  pollLabLog(resp.job_id, logBox);
}

async function labStopAll() {
  const logCard  = document.getElementById("lab-log-card");
  const logBox   = document.getElementById("lab-log");
  document.getElementById("lab-log-title").textContent = "⏹ 停止所有服務";
  logCard.style.display = "block";
  logBox.innerHTML = "";
  const resp = await fetch("/api/lab/stop-all", {method:"POST"}).then(r=>r.json());
  if (resp.job_id) pollLabLog(resp.job_id, logBox);
}

async function labStartAll() {
  const logCard  = document.getElementById("lab-log-card");
  const logBox   = document.getElementById("lab-log");
  document.getElementById("lab-log-title").textContent = "▶ 啟動所有服務";
  logCard.style.display = "block";
  logBox.innerHTML = "";
  const resp = await fetch("/api/lab/start-all", {method:"POST"}).then(r=>r.json());
  if (resp.job_id) pollLabLog(resp.job_id, logBox);
}

function pollLabLog(jobId, logBox) {
  if (labPollTimer) clearInterval(labPollTimer);
  labPollTimer = setInterval(async () => {
    const j = await fetch(`/api/status/${jobId}`).then(r=>r.json());
    logBox.innerHTML = (j.logs||[]).map(l =>
      `<div style="font-size:.75rem;color:${l.includes("✓")?"#22c55e":l.includes("錯誤")?"#ef4444":"#94a3b8"}">${l}</div>`
    ).join("");
    logBox.scrollTop = logBox.scrollHeight;
    if (j.status === "done" || j.status === "failed") {
      clearInterval(labPollTimer);
      // 完成後重新整理群組狀態
      setTimeout(loadLabGroups, 800);
    }
  }, 1200);
}
