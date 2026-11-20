<script setup>
import { computed } from 'vue'
import { store } from '../store'
import { statusOf, fmtTime, parse, KIND } from '../constants'

const rows = computed(() => store.runs.slice(0, 20))
const statOf = (r) => parse(r.stats, null)
const statItems = (r) => {
  const s = statOf(r)
  if (!s) return []
  return [
    ['发现', s.discovered], ['送审', s.reviews], ['触达', s.greeted],
    ['FAQ', s.faq_answered], ['约面', s.interest], ['转人工', s.escalated], ['失败', s.failures]
  ].filter(([, v]) => v !== undefined && v !== null)
}
</script>

<template>
  <div class="panel">
    <div class="panel-head">
      <span class="panel-title">运行记录</span>
      <span class="count-text">最近 {{ rows.length }} 次任务</span>
    </div>
    <el-table :data="rows">
      <el-table-column label="#" width="70">
        <template #default="{ row }"><span class="muted">#{{ row.id }}</span></template>
      </el-table-column>
      <el-table-column label="类型" width="130">
        <template #default="{ row }">{{ KIND[row.kind] || row.kind }}</template>
      </el-table-column>
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="statusOf(row.state).type" effect="light" round>
            <el-icon v-if="row.state === 'RUNNING'" class="spin" style="vertical-align: -2px; margin-right: 3px"><Loading /></el-icon>{{ statusOf(row.state).label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="110">
        <template #default="{ row }"><span class="muted">{{ fmtTime(row.createdAt, 'time') }}</span></template>
      </el-table-column>
      <el-table-column label="结果摘要" min-width="280">
        <template #default="{ row }">
          <div v-if="statItems(row).length" class="stat-chips">
            <span v-for="[k, v] in statItems(row)" :key="k" class="stat-chip">{{ k }} <b>{{ v }}</b></span>
          </div>
          <span v-else class="muted">-</span>
        </template>
      </el-table-column>
      <el-table-column label="错误" width="100">
        <template #default="{ row }">
          <el-tooltip v-if="row.error" :content="row.error" placement="top" effect="dark">
            <el-link type="danger" :underline="false">查看错误</el-link>
          </el-tooltip>
          <span v-else class="muted">-</span>
        </template>
      </el-table-column>
      <template #empty><el-empty description="暂无运行记录" /></template>
    </el-table>
  </div>
</template>