/* HirePilot 前端逻辑（原生 JS，同源 API） */
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const STATUS = { DISCOVERED: "已发现", SCORED: "已评分", REJECTED: "已拒绝", PENDING_REVIEW: "待审核", APPROVED: "已批准", GREETED: "已触达", CHATTING: "沟通中", INTERVIEW: "已约面", ESCALATED: "转人工", CLOSED: "已关闭", PENDING: "排队中", RUNNING: "执行中", DONE: "完成", FAILED: "失败" };
const KIND = { SCREEN: "筛选简历", ENGAGE: "触达与回复" };
const state = { jobs: [], jobId: null, tab: "reviews", reviews: [], candidates: [], runs: [], dash: null, online: false };

async function api(path, opts = {}) {
  const r = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  if (!r.ok) {
    const msg = r.status === 409 ? "冲突：该职位已有排队/执行中的任务，或状态不允许此操作" : `请求失败 HTTP ${r.status}`;
    throw new Error(msg);
  }
  return r.status === 204 ? null : r.json();
}
function toast(msg, err = false) {
  const t = $("#toast");
  t.textContent = msg; t.className = "toast" + (err ? " err" : "");
  clearTimeout(t._h); t._h = setTimeout(() => t.classList.add("hidden"), 3200);
}
const badge = (s) => `<span class="badge b-${s}">${STATUS[s] || s}</span>`;
const parse = (s, d = {}) => { try { return typeof s === "string" ? JSON.parse(s) : (s || d); } catch { return d; } };

async function loadJobs() {
  state.jobs = await api("/api/jobs");
  const sel = $("#job-select");
  sel.innerHTML = state.jobs.map((j) => `<option value="${j.id}">${esc(j.title)}</option>`).join("");
  if (!state.jobId && state.jobs.length) state.jobId = state.jobs[0].id;
  sel.value = state.jobId;
}

async function refresh() {
  if (!state.jobId) return;
  const [dash, reviews, cands, runs, online] = await Promise.all([
    api(`/api/dashboard?jobId=${state.jobId}`), api("/api/reviews?decision=PENDING"),
    api(`/api/candidates?jobId=${state.jobId}`), api(`/api/runs?jobId=${state.jobId}`), api("/api/worker/online"),
  ]);
  state.dash = dash; state.candidates = cands; state.runs = runs; state.online = online.online;
  state.reviews = reviews.filter((r) => { const c = cands.find((x) => x.id === r.candidateId); return c && c.jobId === state.jobId; });
  renderHeader(); renderFunnel(); renderTab();
}

function renderHeader() {
  $("#worker-dot").className = "dot " + (state.online ? "on" : "off");
  $("#worker-text").textContent = state.online ? "Worker 在线" : "Worker 离线（启动: python main.py --serve）";
  const active = state.runs.some((r) => r.state === "PENDING" || r.state === "RUNNING");
  $("#run-banner").classList.toggle("hidden", !active);
  for (const id of ["#btn-screen", "#btn-engage"]) {
    const b = $(id); b.disabled = active || !state.online;
    b.title = !state.online ? "需先启动 Worker 守护进程" : active ? "有任务正在执行" : "";
  }
  const n = state.reviews.length;
  const pill = $("#review-count"); pill.textContent = n; pill.className = "pill" + (n ? "" : " zero");
}

function renderFunnel() {
  const f = state.dash?.funnel || {};
  const cards = [
    ["PENDING_REVIEW", "待审核", "hot"], ["APPROVED", "已批准", ""], ["GREETED", "已触达", ""],
    ["CHATTING", "沟通中", ""], ["INTERVIEW", "已约面", "good"], ["ESCALATED", "转人工", "bad"],
    ["REJECTED", "已拒绝", ""], ["CLOSED", "已关闭", ""],
  ];
  $("#funnel").innerHTML = cards.map(([k, lbl, cls]) =>
    `<div class="fcard ${cls}"><div class="num">${f[k] ?? 0}</div><div class="lbl">${lbl}</div></div>`).join("");
}

function renderTab() {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === state.tab));
  for (const t of ["reviews", "candidates", "runs"]) $(`#tab-${t}`).classList.toggle("hidden", t !== state.tab);
  if (state.tab === "reviews") renderReviews();
  else if (state.tab === "candidates") renderCandidates();
  else renderRuns();
}

function renderReviews() {
  const box = $("#tab-reviews");
  if (!state.reviews.length) { box.innerHTML = `<div class="empty">暂无待审核项。点击右上「筛选简历」让 Agent 开始工作。</div>`; return; }
  box.innerHTML = state.reviews.map((r) => {
    const c = state.candidates.find((x) => x.id === r.candidateId) || {};
    const sr = parse(c.scoreReason);
    return `<div class="review-card">
      <div class="review-head"><span class="name">${esc(c.name)}</span>
        <span class="score ${(c.score || 0) >= 80 ? "high" : ""}">${c.score ?? "-"} 分</span>
        ${c.hardPass ? '<span class="chip">硬条件通过</span>' : '<span class="badge b-ESCALATED">硬条件不符</span>'}
        <span class="muted">${esc(c.title || "")}</span></div>
      <ul class="reasons">${(sr.reasons || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul>
      ${(sr.risks || []).length ? `<ul class="risks">${sr.risks.map((x) => `<li>⚠ ${esc(x)}</li>`).join("")}</ul>` : ""}
      <textarea id="msg-${r.id}" rows="3">${esc(r.proposedMessage)}</textarea>
      <div class="review-actions">
        <button class="btn red" onclick="decide(${r.id},false)">否决</button>
        <button class="btn green" onclick="decide(${r.id},true)">批准并进入触达队列</button>
      </div></div>`;
  }).join("");
}

async function decide(id, approve) {
  try {
    if (approve) {
      const msg = $(`#msg-${id}`).value;
      await api(`/api/reviews/${id}/approve`, { method: "POST", body: JSON.stringify({ message: msg }) });
      toast("已批准，点「执行触达与回复」发送");
    } else {
      await api(`/api/reviews/${id}/reject`, { method: "POST", body: JSON.stringify({ note: "HR 人工否决" }) });
      toast("已否决");
    }
    refresh();
  } catch (e) { toast(e.message, true); }
}

function renderCandidates() {
  const box = $("#tab-candidates");
  if (!state.candidates.length) { box.innerHTML = `<div class="empty">暂无候选人</div>`; return; }
  const rows = [...state.candidates].sort((a, b) => (b.score || 0) - (a.score || 0)).map((c) =>
    `<tr class="clickable" onclick="openCand(${c.id})"><td><b>${esc(c.name)}</b></td>
     <td><span class="score ${(c.score || 0) >= 80 ? "high" : ""}">${c.score ?? "-"}</span></td>
     <td>${c.hardPass ? "✓" : "✗"}</td><td>${badge(c.status)}</td>
     <td class="muted">${(c.updatedAt || "").replace("T", " ").slice(0, 19)}</td></tr>`).join("");
  box.innerHTML = `<table><thead><tr><th>姓名</th><th>评分</th><th>硬条件</th><th>状态</th><th>更新时间</th></tr></thead><tbody>${rows}</tbody></table>`;
}

async function openCand(id) {
  const d = await api(`/api/candidates/${id}`);
  const c = d.candidate, p = parse(c.profile), sr = parse(c.scoreReason);
  $("#cand-title").innerHTML = `${esc(c.name)} ${badge(c.status)} <span class="score">${c.score ?? "-"} 分</span>`;
  $("#cand-body").innerHTML = `
    <div class="chips"><span class="chip">${p.years ?? "?"} 年经验</span><span class="chip">${esc(p.degree || "?")}</span>
      ${(p.skills || []).map((s) => `<span class="chip">${esc(s)}</span>`).join("")}</div>
    <div class="section-title">评分理由</div><ul class="reasons">${(sr.reasons || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul>
    ${(sr.risks || []).length ? `<div class="section-title">风险提示</div><ul class="risks">${sr.risks.map((x) => `<li>⚠ ${esc(x)}</li>`).join("")}</ul>` : ""}
    <div class="section-title">简历原文</div><pre class="resume">${esc(c.resumeText)}</pre>
    <div class="section-title">聊天记录（${d.messages.length}）</div>
    <div class="chat">${d.messages.map((m) => `<div class="bubble ${m.direction === "OUT" ? "out" : "in"}">${esc(m.content)}${m.intent ? `<span class="intent">意图: ${m.intent}</span>` : ""}</div>`).join("") || '<span class="muted">暂无消息</span>'}</div>`;
  $("#modal-cand").classList.remove("hidden");
}

function renderRuns() {
  const box = $("#tab-runs");
  if (!state.runs.length) { box.innerHTML = `<div class="empty">暂无运行记录</div>`; return; }
  const rows = state.runs.slice(0, 20).map((r) => {
    const s = parse(r.stats);
    const sum = r.stats ? `发现${s.discovered ?? 0} 送审${s.reviews ?? 0} 触达${s.greeted ?? 0} FAQ${s.faq_answered ?? 0} 约面${s.interest ?? 0} 转人工${s.escalated ?? 0} 失败${s.failures ?? 0}` : "";
    return `<tr><td>#${r.id}</td><td>${KIND[r.kind] || r.kind}</td><td>${badge(r.state)}</td>
      <td class="muted">${(r.createdAt || "").replace("T", " ").slice(11, 19)}</td>
      <td class="muted">${sum}</td><td class="muted" title="${esc(r.error || "")}">${r.error ? "查看错误" : ""}</td></tr>`;
  }).join("");
  box.innerHTML = `<table><thead><tr><th>#</th><th>类型</th><th>状态</th><th>创建时间</th><th>结果摘要</th><th>错误</th></tr></thead><tbody>${rows}</tbody></table>`;
}

async function startRun(kind) {
  try {
    await api("/api/runs", { method: "POST", body: JSON.stringify({ jobId: state.jobId, kind }) });
    toast(kind === "SCREEN" ? "已排队：筛选简历" : "已排队：触达与回复");
    refresh();
  } catch (e) { toast(e.message, true); }
}

async function createJob() {
  const faq = {};
  $("#j-faq").value.split("\n").forEach((line) => {
    const i = line.indexOf(":") >= 0 ? line.indexOf(":") : line.indexOf("：");
    if (i > 0) faq[line.slice(0, i).trim()] = line.slice(i + 1).trim();
  });
  const job = {
    title: $("#j-title").value.trim(), jdText: $("#j-jd").value.trim(),
    hardFilters: JSON.stringify({ minYears: +$("#j-years").value || 0, degree: $("#j-degree").value, mustSkills: $("#j-skills").value.split(/[,，]/).map((s) => s.trim()).filter(Boolean) }),
    rubric: JSON.stringify({ weights: { skill: 40, experience: 30, education: 20, stability: 10 }, rejectLine: +$("#j-reject").value || 60 }),
    faq: JSON.stringify(faq), greetingStyle: $("#j-style").value, dailyLimit: 20,
  };
  if (!job.title) { toast("请填写职位名称", true); return; }
  try {
    const j = await api("/api/jobs", { method: "POST", body: JSON.stringify(job) });
    state.jobId = j.id; await loadJobs(); $("#modal-job").classList.add("hidden");
    toast(`职位「${j.title}」已创建`); refresh();
  } catch (e) { toast(e.message, true); }
}

document.addEventListener("click", (e) => {
  if (e.target.dataset.close !== undefined || e.target.classList.contains("modal"))
    e.target.closest(".modal")?.classList.add("hidden");
});
$("#job-select").onchange = (e) => { state.jobId = +e.target.value; refresh(); };
$("#btn-new-job").onclick = () => $("#modal-job").classList.remove("hidden");
$("#btn-create-job").onclick = createJob;
$("#btn-screen").onclick = () => startRun("SCREEN");
$("#btn-reset").onclick = async () => {
  if (!confirm("清空本职位的候选人/审核/消息/运行记录？")) return;
  try { await api(`/api/dev/reset?jobId=${state.jobId}`, { method: "POST" }); toast("已重置，可重新筛选"); refresh(); }
  catch (e) { toast(e.message, true); }
};
$("#btn-engage").onclick = () => startRun("ENGAGE");
document.querySelectorAll(".tab").forEach((t) => (t.onclick = () => { state.tab = t.dataset.tab; renderTab(); }));

(async function init() {
  await loadJobs();
  await refresh();
  setInterval(refresh, 3000);
})();