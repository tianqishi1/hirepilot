<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createJob } from '../store'

const visible = defineModel({ type: Boolean, default: false })
const saving = ref(false)
const form = reactive({
  title: '', jdText: '', minYears: 3, degree: '本科', rejectLine: 60,
  skills: 'Java, Spring',
  faq: '薪资范围: 20-30K，14薪，具体面议\n远程政策: 全职远程，每季度一次线下团建\n工时制度: 弹性工作制，双休',
  greetingStyle: '专业、简洁、突出候选人亮点，不超过120字'
})

async function submit() {
  if (!form.title.trim()) { ElMessage.warning('请填写职位名称'); return }
  const faq = {}
  form.faq.split('\n').forEach((line) => {
    const i = line.indexOf(':') >= 0 ? line.indexOf(':') : line.indexOf('：')
    if (i > 0) faq[line.slice(0, i).trim()] = line.slice(i + 1).trim()
  })
  const payload = {
    title: form.title.trim(),
    jdText: form.jdText.trim(),
    hardFilters: JSON.stringify({
      minYears: Number(form.minYears) || 0,
      degree: form.degree,
      mustSkills: form.skills.split(/[,，]/).map((s) => s.trim()).filter(Boolean)
    }),
    rubric: JSON.stringify({ weights: { skill: 40, experience: 30, education: 20, stability: 10 }, rejectLine: Number(form.rejectLine) || 60 }),
    faq: JSON.stringify(faq),
    greetingStyle: form.greetingStyle,
    dailyLimit: 20
  }
  saving.value = true
  try {
    await createJob(payload)
    visible.value = false
    form.title = ''; form.jdText = ''
  } catch (e) { ElMessage.error(e.message) }
  finally { saving.value = false }
}
</script>

<template>
  <el-dialog v-model="visible" title="新建职位" width="640px" :close-on-click-modal="false" destroy-on-close>
    <el-form label-position="top">
      <el-form-item label="职位名称" required>
        <el-input v-model="form.title" placeholder="如：资深Java工程师（远程）" />
      </el-form-item>
      <el-form-item label="JD 描述">
        <el-input v-model="form.jdText" type="textarea" :rows="4" placeholder="岗位职责与要求（Agent 据此评估简历与生成话术）" />
      </el-form-item>
      <el-row :gutter="14">
        <el-col :span="8">
          <el-form-item label="最低年限">
            <el-input-number v-model="form.minYears" :min="0" :max="30" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="最低学历">
            <el-select v-model="form.degree" style="width: 100%">
              <el-option v-for="d in ['本科', '大专', '硕士', '博士']" :key="d" :label="d" :value="d" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="评分拒绝线">
            <el-input-number v-model="form.rejectLine" :min="0" :max="100" style="width: 100%" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="必备技能（逗号分隔）">
        <el-input v-model="form.skills" placeholder="Java, Spring" />
      </el-form-item>
      <el-form-item label="FAQ 知识库（每行一条，格式 键: 值）">
        <el-input v-model="form.faq" type="textarea" :rows="5" placeholder="薪资范围: 20-30K，14薪&#10;远程政策: 全职远程" />
      </el-form-item>
      <el-form-item label="话术风格">
        <el-input v-model="form.greetingStyle" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="submit">创建职位</el-button>
    </template>
  </el-dialog>
</template>