<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PageHeader from '../components/PageHeader.vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const { t } = useI18n()
const message = ref('创建图号 SW-2026-900 的安装板，180x120，4个M6孔，并生成')
const reply = ref('')
const steps = ref([])
const loading = ref(false)

async function send() {
  if (!message.value) return
  loading.value = true
  try {
    const { data } = await api.post('/ai/agent', { message: message.value })
    reply.value = data.reply
    steps.value = data.steps || []
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader :title="t('assistant.title')" :subtitle="t('assistant.subtitle')" />
    <el-input v-model="message" type="textarea" :rows="3" placeholder="描述你要做什么" />
    <div class="row">
      <el-button type="primary" :loading="loading" @click="send">{{ t('assistant.run') }}</el-button>
    </div>

    <el-card v-if="reply" class="card">
      <p>{{ reply }}</p>
      <el-timeline>
        <el-timeline-item v-for="(step, i) in steps" :key="i" :timestamp="step.tool">
          <pre>{{ JSON.stringify(step.result, null, 2) }}</pre>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<style scoped>
.row { margin: 12px 0; }
.card { max-width: 900px; }
pre { margin: 0; white-space: pre-wrap; font-size: 12px; }
</style>
