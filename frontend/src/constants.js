export const STATUS = {
  DISCOVERED: { label: '已发现', type: 'info' },
  SCORED: { label: '已评分', type: 'info' },
  REJECTED: { label: '已拒绝', type: 'danger' },
  PENDING_REVIEW: { label: '待审核', type: 'warning' },
  APPROVED: { label: '已批准', type: 'primary' },
  GREETED: { label: '已触达', type: 'success' },
  CHATTING: { label: '沟通中', type: 'primary' },
  INTERVIEW: { label: '已约面', type: 'success' },
  ESCALATED: { label: '转人工', type: 'danger' },
  CLOSED: { label: '已关闭', type: 'info' },
  PENDING: { label: '排队中', type: 'warning' },
  RUNNING: { label: '执行中', type: 'primary' },
  DONE: { label: '完成', type: 'success' },
  FAILED: { label: '失败', type: 'danger' }
}
export const statusOf = (s) => STATUS[s] || { label: s || '-', type: 'info' }
export const KIND = { SCREEN: '筛选简历', ENGAGE: '触达与回复' }

export const parse = (s, d = {}) => {
  try { return typeof s === 'string' ? JSON.parse(s) : (s ?? d) } catch { return d }
}

export const fmtTime = (t, mode = 'full') => {
  if (!t) return '-'
  const d = new Date(t)
  if (Number.isNaN(d.getTime())) return String(t).replace('T', ' ').slice(0, 19)
  const p = (n) => String(n).padStart(2, '0')
  const date = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
  const time = `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
  return mode === 'time' ? time : `${date} ${time}`
}

export const scoreClass = (s) => (s >= 80 ? 'high' : s >= 60 ? 'mid' : 'low')