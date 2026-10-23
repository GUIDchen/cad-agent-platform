<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PageHeader from '../components/PageHeader.vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const { t } = useI18n()
const prompt = ref('机械安装板，工业设计，干净背景，正交视图')
const negative = ref('低质量，模糊，畸变')
const seed = ref(null)
const width = ref(1024)
const height = ref(768)
const imageUrl = ref('')
const loading = ref(false)

async function generate() {
  if (!prompt.value) return
  loading.value = true
  try {
    const resp = await api.post(
      '/ai/image',
      {
        prompt: prompt.value,
        negative_prompt: negative.value,
        seed: seed.value,
        width: width.value,
        height: height.value,
      },
      { responseType: 'blob' },
    )
    if (imageUrl.value) URL.revokeObjectURL(imageUrl.value)
    imageUrl.value = URL.createObjectURL(resp.data)
    ElMessage.success('已生成（' + (resp.headers['x-image-mode'] || 'mock') + '）')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader :title="t('images.title')" :subtitle="t('images.subtitle')" />
    <el-input v-model="prompt" type="textarea" :rows="3" placeholder="描述要生成的图" />
    <el-input v-model="negative" type="textarea" :rows="2" placeholder="负向提示词（可选）" style="margin-top: 8px" />
    <div class="row">
      <el-input-number v-model="seed" :min="0" :max="2147483647" placeholder="seed" controls-position="right" style="width: 150px" />
      <el-select v-model="width" style="width: 120px">
        <el-option :value="512" label="512" />
        <el-option :value="1024" label="1024" />
        <el-option :value="1536" label="1536" />
      </el-select>
      <el-select v-model="height" style="width: 120px">
        <el-option :value="512" label="512" />
        <el-option :value="768" label="768" />
        <el-option :value="1024" label="1024" />
      </el-select>
      <el-button type="primary" :loading="loading" @click="generate">{{ t('images.generate') }}</el-button>
    </div>
    <el-card v-if="imageUrl" class="card">
      <img :src="imageUrl" class="result" alt="generated" />
    </el-card>
  </div>
</template>

<style scoped>
.row { display: flex; gap: 8px; margin: 12px 0; }
.card { max-width: 900px; }
.result { width: 100%; display: block; }
</style>
