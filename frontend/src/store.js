import { reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from './api'

/* 全局控制台状态：3s 轮询刷新，所有组件共享 */
export const store = reactive({
  jobs: [],
  jobId: null,
  tab: 'reviews',
  dash: null,
  reviews: [],
  candidates: [],
  runs: [],
  online: false,
  ready: false,
  refreshError: false
})

export const activeRun = computed(() =>
  store.runs.some((r) => r.state === 'PENDING' || r.state === 'RUNNING'))

export const currentJob = computed(() =>
  store.jobs.find((j) => j.id === store.jobId) || null)

export async function loadJobs() {
  store.jobs = await api.jobs()
  if (!store.jobId && store.jobs.length) store.jobId = store.jobs[0].id
}

export async function refresh() {
  if (!store.jobId) { store.ready = true; return }
  try {
    const [dash, reviews, cands, runs, online] = await Promise.all([
      api.dashboard(store.jobId),
      api.reviews(),
      api.candidates(store.jobId),
      api.runs(store.jobId),
      api.workerOnline()
    ])
    store.dash = dash
    store.candidates = cands
    store.runs = runs
    store.online = !!online.online
    store.reviews = reviews.filter((r) => {
      const c = cands.find((x) => x.id === r.candidateId)
      return c && c.jobId === store.jobId
    })
    store.refreshError = false
  } catch (e) {
    store.refreshError = true
    console.error('refresh failed', e)
  } finally {
    store.ready = true
  }
}

export async function startRun(kind) {
  try {
    await api.startRun(store.jobId, kind)
    ElMessage.success(kind === 'SCREEN' ? '已排队：筛选简历' : '已排队：触达与回复')
    refresh()
  } catch (e) { ElMessage.error(e.message) }
}

export async function decide(id, approve, message) {
  if (approve) {
    await api.approve(id, message)
    ElMessage.success('已批准，点「执行触达与回复」发送')
  } else {
    await api.reject(id)
    ElMessage.success('已否决')
  }
  refresh()
}

export async function resetJob() {
  await api.reset(store.jobId)
  ElMessage.success('已重置，可重新筛选')
  refresh()
}

export async function createJob(payload) {
  const j = await api.createJob(payload)
  store.jobId = j.id
  await loadJobs()
  ElMessage.success(`职位「${j.title}」已创建`)
  refresh()
  return j
}