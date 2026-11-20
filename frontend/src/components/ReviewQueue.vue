<script setup>
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { store, decide } from '../store'
import { parse, scoreClass } from '../constants'

const emit = defineEmits(['open-candidate'])
const drafts = reactive({})   // reviewId -> 编辑后的话术
const busy = reactive({})     // reviewId -> bool

const candidateOf = (r) => store.candidates.find((x) => x.id === r.candidateId) || {}
const reasonsOf = (r) => parse(candidateOf(r).scoreReason).reasons || []
const risksOf = (r) => parse(candidateOf(r).scoreReason).risks || []
const profileOf = (r) => parse(candidateOf(r).profile)
const draftOf = (r) => drafts[r.id] ?? r.proposedMessage ?? ''

async function onDecide(r, approve) {
  busy[r.id] = true
  try {
    await decide(r.id, approve, approve ? draftOf(r) : undefined)
    delete drafts[r.id]
  } catch (e) { ElMessage.error(e.message) }
  finally { busy[r.id] = false }
}
</script>

<template>
  <div v-if="!store.reviews.length" class="panel empty-wrap">
    <el-empty description="暂无待审核项。点击右上「筛选简历」让 Agent 开始工作。" />
  </div>
  <div v-else class="review-list">
    <div v-for="r in store.reviews" :key="r.id" class="review-card">
      <div class="review-head">
        <div class="avatar">{{ (candidateOf(r).name || '?').slice(0, 1) }}</div>
        <div>
          <div class="review-name">
            <el-link type="primary" :underline="false" @click="emit('open-candidate', r.candidateId)">{{ candidateOf(r).name }}</el-link>
          </div>
          <div class="review-sub">{{ profileOf(r).years ?? '?' }} 年经验 · {{ profileOf(r).degree || '学历未知' }}</div>
        </div>
        <el-tag v-if="candidateOf(r).hardPass" type="success" effect="light" round>硬条件通过</el-tag>
        <el-tag v-else type="danger" effect="light" round>硬条件不符</el-tag>
        <span class="score-pill" :class="scoreClass(candidateOf(r).score || 0)">{{ candidateOf(r).score ?? '-' }} 分</span>
      </div>

      <div class="section-label">评分理由</div>
      <ul class="reason-list good">
        <li v-for="(x, i) in reasonsOf(r)" :key="i"><el-icon><CircleCheck /></el-icon><span>{{ x }}</span></li>
      </ul>
      <template v-if="risksOf(r).length">
        <div class="section-label">风险提示</div>
        <ul class="reason-list risk">
          <li v-for="(x, i) in risksOf(r)" :key="i"><el-icon><WarningFilled /></el-icon><span>{{ x }}</span></li>
        </ul>
      </template>

      <div class="section-label">拟发送话术（可修改后批准）</div>
      <el-input type="textarea" :rows="3" :model-value="draftOf(r)"
        @update:model-value="drafts[r.id] = $event" placeholder="Agent 生成的个性化触达话术" />
      <div class="review-actions">
        <el-button type="danger" plain :loading="busy[r.id]" @click="onDecide(r, false)">否决</el-button>
        <el-button type="success" :loading="busy[r.id]" @click="onDecide(r, true)">批准并进入触达队列</el-button>
      </div>
    </div>
  </div>
</template>