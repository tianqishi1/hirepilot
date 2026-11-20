<script setup>
defineProps({ funnel: { type: Object, default: () => ({}) } })
const cards = [
  { key: 'PENDING_REVIEW', label: '待审核', cls: 'hot' },
  { key: 'APPROVED', label: '已批准', cls: '' },
  { key: 'GREETED', label: '已触达', cls: '' },
  { key: 'CHATTING', label: '沟通中', cls: '' },
  { key: 'INTERVIEW', label: '已约面', cls: 'good' },
  { key: 'ESCALATED', label: '转人工', cls: 'bad' },
  { key: 'REJECTED', label: '已拒绝', cls: '' },
  { key: 'CLOSED', label: '已关闭', cls: '' }
]
</script>

<template>
  <section class="funnel">
    <div v-for="c in cards" :key="c.key" class="fcard" :class="c.cls">
      <div class="num">{{ funnel[c.key] ?? 0 }}</div>
      <div class="lbl">{{ c.label }}</div>
    </div>
  </section>
</template>