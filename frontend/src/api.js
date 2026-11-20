/* 同源 REST 封装（开发期由 Vite 代理到 :8080） */
async function request(path, opts = {}) {
  const r = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...opts })
  if (!r.ok) {
    let msg = r.status === 409
      ? '冲突：该职位已有排队/执行中的任务，或状态不允许此操作'
      : `请求失败 HTTP ${r.status}`
    try { const b = await r.json(); if (b && b.message) msg = b.message } catch { /* ignore */ }
    throw new Error(msg)
  }
  return r.status === 204 ? null : r.json()
}

export const api = {
  jobs: () => request('/api/jobs'),
  createJob: (job) => request('/api/jobs', { method: 'POST', body: JSON.stringify(job) }),
  dashboard: (jobId) => request(`/api/dashboard?jobId=${jobId}`),
  reviews: () => request('/api/reviews?decision=PENDING'),
  approve: (id, message) => request(`/api/reviews/${id}/approve`, { method: 'POST', body: JSON.stringify({ message }) }),
  reject: (id) => request(`/api/reviews/${id}/reject`, { method: 'POST', body: JSON.stringify({ note: 'HR 人工否决' }) }),
  candidates: (jobId) => request(`/api/candidates?jobId=${jobId}`),
  candidate: (id) => request(`/api/candidates/${id}`),
  runs: (jobId) => request(`/api/runs?jobId=${jobId}`),
  startRun: (jobId, kind) => request('/api/runs', { method: 'POST', body: JSON.stringify({ jobId, kind }) }),
  workerOnline: () => request('/api/worker/online'),
  reset: (jobId) => request(`/api/dev/reset?jobId=${jobId}`, { method: 'POST' })
}