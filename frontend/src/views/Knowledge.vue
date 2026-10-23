<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
import api from '../api'

const { t } = useI18n()
const docs = ref([])
const hits = ref([])
const query = ref('')
const dialog = ref(false)
const indexing = ref(false)
const editingId = ref(null)
const historyDialog = ref(false)
const historyTitle = ref('')
const historyDoc = ref(null)
const versions = ref([])
const trashDialog = ref(false)
const trashDocs = ref([])
const role = localStorage.getItem('role')
const form = reactive({ title: '', content: '' })

async function load() {
  docs.value = (await api.get('/rag/documents')).data
}

async function search() {
  if (!query.value.trim()) {
    hits.value = []
    return
  }
  hits.value = (await api.get('/rag/search', { params: { q: query.value } })).data
}

async function reindex() {
  indexing.value = true
  try {
    const { data } = await api.post('/rag/reindex', null, { params: { force: true } })
    ElMessage.success('已重建 ' + data.documents + ' 篇 / ' + data.chunks + ' 块')
    await load()
  } finally {
    indexing.value = false
  }
}

function openCreate() {
  editingId.value = null
  form.title = ''
  form.content = ''
  dialog.value = true
}

function openEdit(row) {
  editingId.value = row.id
  form.title = row.title
  form.content = row.content
  dialog.value = true
}

async function openTrash() {
  trashDocs.value = (await api.get('/rag/trash')).data
  trashDialog.value = true
}

async function restoreTrash(row) {
  await api.post('/rag/documents/' + row.id + '/restore')
  ElMessage.success('已恢复')
  await openTrash()
  await load()
}

async function purgeTrash(row) {
  await ElMessageBox.confirm('确认彻底删除 ' + row.title + '？')
  await api.delete('/rag/documents/' + row.id + '/purge')
  ElMessage.success('已彻底删除')
  await openTrash()
}

async function openHistory(row) {
  historyDoc.value = row
  historyTitle.value = row.title
  versions.value = (await api.get('/rag/documents/' + row.id + '/versions')).data
  historyDialog.value = true
}

async function restore(version) {
  await api.post('/rag/documents/' + historyDoc.value.id + '/versions/' + version.id + '/restore')
  ElMessage.success('已恢复')
  historyDialog.value = false
  await load()
}

async function remove(row) {
  await ElMessageBox.confirm('确认删除 ' + row.title + '？')
  await api.delete('/rag/documents/' + row.id)
  ElMessage.success('已删除')
  await load()
}

async function save() {
  if (!form.title || !form.content) return
  if (editingId.value) {
    await api.patch('/rag/documents/' + editingId.value, form)
    ElMessage.success('已更新')
  } else {
    await api.post('/rag/documents', form)
    ElMessage.success('已添加')
  }
  form.title = ''
  form.content = ''
  editingId.value = null
  dialog.value = false
  await load()
}

onMounted(load)
</script>

<template>
  <div class="page">
    <PageHeader :title="t('knowledge.title')" :subtitle="t('knowledge.subtitle')">
      <el-button v-if="role !== 'viewer'" :loading="indexing" @click="reindex">重建索引</el-button>
      <el-button v-if="role !== 'viewer'" @click="openTrash">回收站</el-button>
      <el-button type="primary" @click="openCreate">{{ t('knowledge.new') }}</el-button>
    </PageHeader>

    <el-card class="search">
      <div class="row">
        <el-input v-model="query" :placeholder="t('knowledge.search')" @keyup.enter="search" />
        <el-button type="primary" @click="search">{{ t('knowledge.searchBtn') }}</el-button>
      </div>
      <div v-if="hits.length" class="hits">
        <div v-for="hit in hits" :key="hit.id" class="hit">
          <strong>{{ hit.title }}</strong>
          <span>score {{ hit.score }}</span>
          <p>{{ hit.snippet }}</p>
        </div>
      </div>
      <el-empty v-else-if="query" :description="t('knowledge.empty')" :image-size="70" />
    </el-card>

    <el-card :header="t('knowledge.docs')" class="docs">
      <el-table :data="docs">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" :label="t('knowledge.titleCol')" />
        <el-table-column prop="created_at" :label="t('knowledge.created')" width="190" />
        <el-table-column :label="t('knowledge.content')" min-width="260">
          <template #default="{ row }">
            <span class="snippet">{{ row.content.slice(0, 80) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="170">
          <template #default="{ row }">
            <el-button v-if="role !== 'viewer'" link @click="openEdit(row)">编辑</el-button>
            <el-button link @click="openHistory(row)">历史</el-button>
            <el-button v-if="role !== 'viewer'" link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialog" :title="editingId ? '编辑文档' : t('knowledge.dialog')" width="620px">
      <el-form label-width="70px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="内容"><el-input v-model="form.content" type="textarea" :rows="6" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">{{ t('knowledge.cancel') }}</el-button>
        <el-button type="primary" @click="save">{{ t('knowledge.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="historyDialog" :title="'版本历史 · ' + historyTitle" width="720px">
      <el-table :data="versions">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="created_at" label="时间" width="190" />
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <el-button v-if="role !== 'viewer'" link @click="restore(row)">恢复</el-button>
          </template>
        </el-table-column>
        <template #empty><el-empty description="暂无历史版本" :image-size="60" /></template>
      </el-table>
    </el-dialog>

    <el-dialog v-model="trashDialog" title="回收站" width="640px">
      <el-table :data="trashDocs">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button link @click="restoreTrash(row)">恢复</el-button>
            <el-button link type="danger" @click="purgeTrash(row)">彻底删除</el-button>
          </template>
        </el-table-column>
        <template #empty><el-empty description="回收站为空" :image-size="60" /></template>
      </el-table>
    </el-dialog>
  </div>
</template>

<style scoped>
.search { margin-bottom: 16px; }
.row { display: flex; gap: 8px; }
.hits { margin-top: 14px; display: flex; flex-direction: column; gap: 10px; }
.hit { border-left: 3px solid #2563eb; background: #f8fafc; padding: 10px 12px; border-radius: 0 8px 8px 0; }
.hit span { color: #94a3b8; font-size: 11px; margin-left: 8px; }
.hit p { margin: 6px 0 0; color: #475569; font-size: 13px; }
.snippet { color: #64748b; }
.docs { margin-top: 16px; }
</style>
