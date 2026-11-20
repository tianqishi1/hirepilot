<script setup>
import { onMounted, onBeforeUnmount, ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { store, refresh, loadJobs, startRun, resetJob, activeRun } from './store'
import FunnelStats from './components/FunnelStats.vue'
import ReviewQueue from './components/ReviewQueue.vue'
import CandidateTable from './components/CandidateTable.vue'
import RunTable from './components/RunTable.vue'
import JobDialog from './components/JobDialog.vue'
import CandidateDrawer from './components/CandidateDrawer.vue'

const jobDialogVisible = ref(false)
const drawerCandId = ref(null)
let timer = null

const navs = [
  { key: 'reviews', label: '审核队列', icon: 'Stamp' },
  { key: 'candidates', label: '候选人', icon: 'User' },
  { key: 'runs', label: '运行记录', icon: 'List' }
]

const runDisabled = computed(() => !store.online || activeRun.value)
const runTip = computed(() => !store.online
  ? '需先启动 Worker 守护进程：python worker/main.py --serve'
  : activeRun.value ? '有任务正在排队/执行中' : '')

async function onReset() {
  try {
    await ElMessageBox.confirm('清空本职位的候选人 / 审核 / 消息 / 运行记录？此操作仅用于演示重置。', '重置职位数据', {
      confirmButtonText: '确认重置', cancelButtonText: '取消', type: 'warning'
    })
  } catch { return }
  try { await resetJob() } catch (e) { ElMessage.error(e.message) }
}

function openCandidate(id) { drawerCandId.value = id }

onMounted(async () => {
  try { await loadJobs() } catch (e) { ElMessage.error('无法连接后台：' + e.message) }
  await refresh()
  timer = setInterval(refresh, 3000)
})
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <el-container class="layout">
    <el-aside width="232px" class="sidebar">
      <div class="brand">
        <div class="brand-logo">H</div>
        <div>
          <div class="brand-name">HirePilot</div>
          <div class="brand-sub">AI 招聘运营台</div>
        </div>
      </div>
      <nav class="nav">
        <button v-for="n in navs" :key="n.key" class="nav-item" :class="{ active: store.tab === n.key }" @click="store.tab = n.key">
          <el-icon><component :is="n.icon" /></el-icon>
          <span>{{ n.label }}</span>
          <span v-if="n.key === 'reviews'" class="nav-badge" :class="{ hot: store.reviews.length }">{{ store.reviews.length }}</span>
          <span v-else-if="n.key === 'candidates'" class="nav-badge">{{ store.candidates.length }}</span>
        </button>
      </nav>
      <div class="sidebar-foot">
        <div class="worker-card">
          <span class="worker-dot" :class="store.online ? 'on' : 'off'" />
          <span>{{ store.online ? 'Worker 在线' : 'Worker 离线' }}</span>
        </div>
        <div v-if="!store.online" class="worker-hint">启动守护进程：<br><code>python worker/main.py --serve</code></div>
      </div>
    </el-aside>

    <el-container class="main-wrap">
      <el-header class="topbar">
        <span class="page-title">当前职位</span>
        <el-select v-model="store.jobId" class="job-select" placeholder="选择职位" @change="refresh">
          <el-option v-for="j in store.jobs" :key="j.id" :label="j.title" :value="j.id" />
        </el-select>
        <div class="topbar-spacer" />
        <el-button plain :icon="'Plus'" @click="jobDialogVisible = true">新职位</el-button>
        <el-button plain type="danger" :icon="'RefreshLeft'" @click="onReset">重置</el-button>
        <el-tooltip :disabled="!runDisabled" :content="runTip" placement="bottom">
          <el-button type="primary" :icon="'Search'" :disabled="runDisabled" @click="startRun('SCREEN')">筛选简历</el-button>
        </el-tooltip>
        <el-tooltip :disabled="!runDisabled" :content="runTip" placement="bottom">
          <el-button type="primary" :icon="'Promotion'" :disabled="runDisabled" @click="startRun('ENGAGE')">执行触达与回复</el-button>
        </el-tooltip>
      </el-header>

      <el-main class="content">
        <el-alert v-if="store.refreshError" class="err-banner" type="error" :closable="false"
          title="后台连接异常，正在自动重试…" show-icon />
        <el-alert v-if="activeRun" class="run-banner" type="info" :closable="false" show-icon>
          <template #title>
            <el-icon class="spin" style="vertical-align: -2px; margin-right: 6px"><Loading /></el-icon>
            Agent 正在执行任务，审核队列与候选人状态将实时刷新…
          </template>
        </el-alert>

        <FunnelStats :funnel="store.dash?.funnel || {}" />

        <ReviewQueue v-if="store.tab === 'reviews'" @open-candidate="openCandidate" />
        <CandidateTable v-else-if="store.tab === 'candidates'" @open-candidate="openCandidate" />
        <RunTable v-else />
      </el-main>
    </el-container>
  </el-container>

  <JobDialog v-model="jobDialogVisible" />
  <CandidateDrawer :candidate-id="drawerCandId" @close="drawerCandId = null" />
</template>