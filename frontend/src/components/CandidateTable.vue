<script setup>
import { ref, computed } from 'vue'
import { store } from '../store'
import { statusOf, fmtTime, scoreClass, STATUS } from '../constants'

const emit = defineEmits(['open-candidate'])
const keyword = ref('')
const statusFilter = ref('')

const statusOptions = Object.entries(STATUS)
  .filter(([k]) => !['PENDING', 'RUNNING', 'DONE', 'FAILED'].includes(k))
  .map(([value, v]) => ({ value, label: v.label }))

const rows = computed(() => {
  let list = [...store.candidates]
  if (statusFilter.value) list = list.filter((c) => c.status === statusFilter.value)
  const kw = keyword.value.trim().toLowerCase()
  if (kw) list = list.filter((c) => (c.name || '').toLowerCase().includes(kw) || (c.externalId || '').toLowerCase().includes(kw))
  return list.sort((a, b) => (b.score || 0) - (a.score || 0))
})
</script>

<template>
  <div class="panel">
    <div class="panel-head">
      <span class="panel-title">候选人</span>
      <div class="table-toolbar">
        <el-input v-model="keyword" placeholder="搜索姓名 / ID" clearable :prefix-icon="'Search'" />
        <el-select v-model="statusFilter" placeholder="全部状态" clearable>
          <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
      </div>
      <span class="count-text">共 {{ rows.length }} 人 · 按评分排序</span>
    </div>
    <el-table :data="rows" row-class-name="clickable-row" highlight-current-row
      @row-click="(row) => emit('open-candidate', row.id)">
      <el-table-column label="姓名" min-width="140">
        <template #default="{ row }">
          <span class="cand-name">{{ row.name }}</span>
          <span class="muted" style="margin-left: 8px; font-size: 12px">{{ row.externalId }}</span>
        </template>
      </el-table-column>
      <el-table-column label="评分" width="90" sortable :sort-by="(row) => row.score || 0">
        <template #default="{ row }">
          <span class="score-num" :class="scoreClass(row.score || 0)">{{ row.score ?? '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="硬条件" width="90" align="center">
        <template #default="{ row }">
          <el-icon v-if="row.hardPass" class="hard-ok"><CircleCheckFilled /></el-icon>
          <el-icon v-else class="hard-no"><CircleCloseFilled /></el-icon>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="statusOf(row.status).type" effect="light" round>{{ statusOf(row.status).label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="更新时间" min-width="160">
        <template #default="{ row }"><span class="muted">{{ fmtTime(row.updatedAt) }}</span></template>
      </el-table-column>
      <template #empty><el-empty description="暂无候选人，点击右上「筛选简历」开始" /></template>
    </el-table>
  </div>
</template>