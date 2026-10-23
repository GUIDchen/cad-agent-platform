<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PageHeader from '../components/PageHeader.vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const { t } = useI18n()
const rows = ref([])
const offset = ref(0)
const limit = 20
const loading = ref(false)
const filters = reactive({ action: '', object_id: '', actor_id: '' })
const range = ref([])

function params() {
  const p = { offset: offset.value, limit }
  if (filters.action) p.action = filters.action
  if (filters.object_id) p.object_id = filters.object_id
  if (filters.actor_id) p.actor_id = Number(filters.actor_id)
  if (range.value?.length === 2) {
    p.start = new Date(range.value[0]).toISOString()
    p.end = new Date(range.value[1]).toISOString()
  }
  return p
}

async function load() {
  loading.value = true
  try {
    rows.value = (await api.get('/audit', { params: params() })).data
  } finally {
    loading.value = false
  }
}

function search() {
  offset.value = 0
  load()
}

function reset() {
  filters.action = ''
  filters.object_id = ''
  filters.actor_id = ''
  range.value = []
  search()
}

function prev() {
  offset.value = Math.max(0, offset.value - limit)
  load()
}

function next() {
  offset.value += limit
  load()
}

async function exportCsv() {
  const p = { ...params(), fmt: 'csv', limit: 5000 }
  const resp = await api.get('/audit', { params: p, responseType: 'blob' })
  const url = URL.createObjectURL(resp.data)
  const a = document.createElement('a')
  a.href = url
  a.download = 'audit.csv'
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('已导出')
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader :title="t('audit.title')" :subtitle="t('audit.subtitle')">
      <el-button type="primary" @click="exportCsv">{{ t('audit.export') }}</el-button>
    </PageHeader>

    <div class="filters">
      <el-input v-model="filters.action" placeholder="action，如 project.create" style="width: 220px" />
      <el-input v-model="filters.object_id" placeholder="对象 ID，如 SW-2026-001" style="width: 220px" />
      <el-input v-model="filters.actor_id" placeholder="操作人 ID" style="width: 120px" />
      <el-date-picker
        v-model="range"
        type="datetimerange"
        start-placeholder="开始时间"
        end-placeholder="结束时间"
        style="width: 360px"
      />
      <el-button type="primary" @click="search">{{ t('audit.query') }}</el-button>
      <el-button @click="reset">{{ t('audit.reset') }}</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" size="small">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="actor_id" :label="t('audit.actor')" width="80" />
      <el-table-column prop="action" :label="t('audit.action')" width="180" />
      <el-table-column prop="object_type" :label="t('audit.type')" width="100" />
      <el-table-column prop="object_id" :label="t('audit.object')" width="160" />
      <el-table-column prop="created_at" :label="t('audit.time')" width="180" />
      <el-table-column prop="detail_json" :label="t('audit.detail')" show-overflow-tooltip />
    </el-table>

    <div class="pager">
      <el-button :disabled="offset === 0" @click="prev">{{ t('audit.prev') }}</el-button>
      <span>offset {{ offset }}</span>
      <el-button :disabled="rows.length < limit" @click="next">{{ t('audit.next') }}</el-button>
    </div>
  </div>
</template>

<style scoped>
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.filters { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.pager { display: flex; gap: 12px; align-items: center; margin-top: 12px; color: #64748b; }
</style>
