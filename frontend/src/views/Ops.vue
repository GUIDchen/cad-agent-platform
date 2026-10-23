<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
import api from '../api'

const rows = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    rows.value = (await api.get('/jobs/dead')).data
  } finally {
    loading.value = false
  }
}

async function clearAll() {
  await ElMessageBox.confirm('确认清空死信列表？')
  await api.delete('/jobs/dead')
  ElMessage.success('已清空')
  await load()
}

async function requeue(row) {
  await api.post('/jobs/' + row.id + '/requeue')
  ElMessage.success('已重排')
  await load()
}

onMounted(load)
</script>

<template>
  <div class="page">
    <PageHeader title="运维" subtitle="死信任务重排；仅管理员可见">
      <el-button @click="load">刷新</el-button>
      <el-button type="danger" @click="clearAll">清空死信</el-button>
    </PageHeader>

    <el-card>
      <el-table :data="rows" v-loading="loading">
        <el-table-column prop="id" label="任务ID" width="220" show-overflow-tooltip />
        <el-table-column prop="drawing_no" label="图号" width="150" />
        <el-table-column prop="title" label="名称" />
        <el-table-column prop="type" label="类型" width="150" />
        <el-table-column prop="attempts" label="尝试" width="80" />
        <el-table-column prop="error" label="错误" show-overflow-tooltip />
        <el-table-column label="操作" width="100" align="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="requeue(row)">重排</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="没有死信任务" :image-size="80" />
        </template>
      </el-table>
    </el-card>
  </div>
</template>
