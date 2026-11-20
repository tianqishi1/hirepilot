<script setup>
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api'
import { parse, statusOf, scoreClass } from '../constants'

const props = defineProps({ candidateId: { type: Number, default: null } })
const emit = defineEmits(['close'])

const visible = ref(false)
const loading = ref(false)
const detail = ref(null)

const c = computed(() => detail.value?.candidate || {})
const profile = computed(() => parse(c.value.profile))
const scoreReason = computed(() => parse(c.value.scoreReason))
const messages = computed(() => detail.value?.messages || [])

watch(() => props.candidateId, async (id) => {
  if (!id) { visible.value = false; return }
  visible.value = true
  loading.value = true
  detail.value = null
  try { detail.value = await api.candidate(id) }
  catch (e) { ElMessage.error(e.message); visible.value = false }
  finally { loading.value = false }
})

function onClosed() { emit('close') }
</script>

<template>
  <el-drawer v-model="visible" size="580px" class="cand-drawer" :destroy-on-close="false" @closed="onClosed">
    <template #header>
      <div class="drawer-title">
        <span>{{ c.name || '候选人详情' }}</span>
        <el-tag v-if="c.status" :type="statusOf(c.status).type" effect="light" round>{{ statusOf(c.status).label }}</el-tag>
        <span class="score-pill" :class="scoreClass(c.score || 0)">{{ c.score ?? '-' }} 分</span>
      </div>
    </template>
    <div v-loading="loading">
      <template v-if="detail">
        <div class="chip-row">
          <el-tag effect="plain" round>{{ profile.years ?? '?' }} 年经验</el-tag>
          <el-tag effect="plain" round>{{ profile.degree || '学历未知' }}</el-tag>
          <el-tag v-for="s in profile.skills || []" :key="s" type="primary" effect="light" round>{{ s }}</el-tag>
        </div>
        <p v-if="profile.highlight" class="muted" style="font-size: 13px; line-height: 1.7">{{ profile.highlight }}</p>

        <div class="section-label">评分理由</div>
        <ul class="reason-list good">
          <li v-for="(x, i) in scoreReason.reasons || []" :key="i"><el-icon><CircleCheck /></el-icon><span>{{ x }}</span></li>
        </ul>
        <template v-if="(scoreReason.risks || []).length">
          <div class="section-label">风险提示</div>
          <ul class="reason-list risk">
            <li v-for="(x, i) in scoreReason.risks" :key="i"><el-icon><WarningFilled /></el-icon><span>{{ x }}</span></li>
          </ul>
        </template>

        <div class="section-label">简历原文</div>
        <pre class="resume-pre">{{ c.resumeText }}</pre>

        <div class="section-label">聊天记录（{{ messages.length }}）</div>
        <div class="chat-box">
          <div v-for="m in messages" :key="m.id" class="bubble" :class="m.direction === 'OUT' ? 'out' : 'in'">
            {{ m.content }}
            <el-tag v-if="m.intent" class="intent-tag" size="small" type="info" effect="plain">意图: {{ m.intent }}</el-tag>
          </div>
          <span v-if="!messages.length" class="muted">暂无消息</span>
        </div>
      </template>
    </div>
  </el-drawer>
</template>