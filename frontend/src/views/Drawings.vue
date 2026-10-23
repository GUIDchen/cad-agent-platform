<script setup>
import { computed, onUnmounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import api from '../api'
import { useCreateDrawing, useDrawingsQuery, useProjectsQuery } from '../queries'

const router = useRouter()
const { t } = useI18n()
const { data: projectsData } = useProjectsQuery()
const { data: drawingsData, isLoading: loading } = useDrawingsQuery()
const projects = computed(() => projectsData.value || [])
const drawings = computed(() => drawingsData.value || [])
const createMutation = useCreateDrawing()
const dialog = ref(false)
const batchDialog = ref(false)
const batchLoading = ref(false)
const progressDialog = ref(false)
const batchJobs = ref([])
const selection = ref([])
let pollTimer = null
const batchForm = reactive({
  length: 180,
  width: 120,
  thickness: 6,
  corner_radius: 0,
  material: '304',
  surface: '拉丝',
  holes: '[{"x":20,"y":20,"d":6.6},{"x":160,"y":20,"d":6.6}]',
})
const keyword = ref('')
const form = reactive({ project_id: null, drawing_no: 'SW-2026-001', title: '' })
const role = localStorage.getItem('role')

watch(projects, (list) => {
  if (!form.project_id && list.length) form.project_id = list[0].id
}, { immediate: true })

const statusMap = computed(() => ({
  draft: { text: t('drawings.statuses.draft'), type: 'info' },
  generating: { text: t('drawings.statuses.generating'), type: 'warning' },
  pending_review: { text: t('drawings.statuses.pending_review'), type: 'primary' },
  approved: { text: t('drawings.statuses.approved'), type: 'success' },
  rejected: { text: t('drawings.statuses.rejected'), type: 'danger' },
  archived: { text: t('drawings.statuses.archived'), type: 'success' },
}))

const filtered = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  if (!query) return drawings.value
  return drawings.value.filter(
    (row) =>
      row.drawing_no.toLowerCase().includes(query) ||
      (row.title || '').toLowerCase().includes(query),
  )
})

const summary = computed(() => [
  { label: t('drawings.all'), value: drawings.value.length },
  { label: t('drawings.pending'), value: drawings.value.filter((d) => d.status === 'pending_review').length },
  { label: t('drawings.approved'), value: drawings.value.filter((d) => d.status === 'approved').length },
])

const terminal = new Set(['done', 'failed', 'canceled', 'dead'])
const jobLabels = { queued: '排队', running: '生成中', done: '完成', failed: '失败', canceled: '取消', dead: '死信' }
const jobTypes = { queued: 'info', running: 'warning', done: 'success', failed: 'danger', canceled: 'info', dead: 'danger' }

async function refreshBatch() {
  const rows = await Promise.all(
    batchJobs.value.map(async (row) => {
      try {
        const { data } = await api.get('/jobs/' + row.job_id)
        return { ...row, status: data.status, error: data.error }
      } catch {
        return row
      }
    }),
  )
  batchJobs.value = rows
  if (rows.length && rows.every((row) => terminal.has(row.status))) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function startPoll() {
  if (pollTimer) clearInterval(pollTimer)
  refreshBatch()
  pollTimer = setInterval(refreshBatch, 2000)
}

onUnmounted(() => clearInterval(pollTimer))

async function batchGenerate() {
  let holes
  try {
    holes = JSON.parse(batchForm.holes)
  } catch {
    ElMessage.error('孔位必须是 JSON 数组')
    return
  }
  batchLoading.value = true
  try {
    const items = selection.value.map((row) => ({ drawing_id: row.id, spec: { ...batchForm, holes } }))
    const selected = [...selection.value]
    const { data } = await api.post('/drawings/batch-generate', { items })
    ElMessage.success('已提交 ' + data.length + ' 个任务')
    batchJobs.value = data.map((job, index) => ({
      job_id: job.job_id,
      drawing_no: selected[index]?.drawing_no || '-',
      status: job.status,
      error: '',
    }))
    batchDialog.value = false
    progressDialog.value = true
    startPoll()
    selection.value = []
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    batchLoading.value = false
  }
}

async function create() {
  try {
    await createMutation.mutateAsync({ ...form })
    ElMessage.success('已创建')
    dialog.value = false
  } catch (e) {
    ElMessage.error(e.message)
  }
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>{{ t('drawings.title') }}</h1>
        <p>{{ t('drawings.subtitle') }}</p>
      </div>
      <div class="page-actions">
        <el-button v-if="role !== 'viewer' && selection.length" :loading="batchLoading" @click="batchDialog = true">
          批量生成 ({{ selection.length }})
        </el-button>
        <el-button v-if="role !== 'viewer'" type="primary" :icon="Plus" @click="dialog = true">
          {{ t('drawings.new') }}
        </el-button>
      </div>
    </div>

    <div class="summary">
      <div v-for="item in summary" :key="item.label" class="chip">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </div>
    </div>

    <el-card class="table-card">
      <div class="table-head">
        <el-input
          v-model="keyword"
          :prefix-icon="Search"
          :placeholder="t('drawings.search')"
          clearable
          style="max-width: 320px"
        />
      </div>

      <el-skeleton v-if="loading" :rows="6" animated />
      <el-table
        v-else
        :data="filtered"
        style="cursor: pointer"
        @row-click="(row) => router.push('/drawings/' + row.id)"
        @selection-change="selection = $event"
      >
        <el-table-column type="selection" width="44" />
        <el-table-column prop="drawing_no" :label="t('drawings.drawingNo')" width="170" />
        <el-table-column prop="title" :label="t('drawings.name')" min-width="200" />
        <el-table-column :label="t('drawings.status')" width="120">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type || 'info'" effect="light" round>
              {{ statusMap[row.status]?.text || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="current_version_id" :label="t('drawings.version')" width="110" align="center" />
        <el-table-column prop="locked_by" :label="t('drawings.lockedBy')" width="100" align="center">
          <template #default="{ row }">{{ row.locked_by || '-' }}</template>
        </el-table-column>
        <template #empty>
          <el-empty :description="t('drawings.empty')" :image-size="90" />
        </template>
      </el-table>
    </el-card>

    <el-dialog v-model="dialog" :title="t('drawings.dialogTitle')" width="480px">
      <el-form label-width="80px">
        <el-form-item :label="t('drawings.project')">
          <el-select v-model="form.project_id" style="width: 100%">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('drawings.drawingNo')">
          <el-input v-model="form.drawing_no" placeholder="SW-2026-001" />
        </el-form-item>
        <el-form-item :label="t('drawings.name')">
          <el-input v-model="form.title" placeholder="例如：安装板" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">{{ t('drawings.cancel') }}</el-button>
        <el-button type="primary" @click="create">{{ t('drawings.create') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="batchDialog" title="批量生成" width="560px">
      <p class="hint">对选中的 {{ selection.length }} 张图纸使用相同参数批量生成。</p>
      <el-form label-width="90px">
        <el-form-item label="长 mm"><el-input-number v-model="batchForm.length" :min="20" /></el-form-item>
        <el-form-item label="宽 mm"><el-input-number v-model="batchForm.width" :min="20" /></el-form-item>
        <el-form-item label="厚 mm"><el-input-number v-model="batchForm.thickness" :min="1" /></el-form-item>
        <el-form-item label="圆角 mm"><el-input-number v-model="batchForm.corner_radius" :min="0" :max="100" /></el-form-item>
        <el-form-item label="材料"><el-input v-model="batchForm.material" /></el-form-item>
        <el-form-item label="表面"><el-input v-model="batchForm.surface" /></el-form-item>
        <el-form-item label="孔位"><el-input v-model="batchForm.holes" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialog = false">取消</el-button>
        <el-button type="primary" :loading="batchLoading" @click="batchGenerate">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="progressDialog" title="批量任务进度" width="680px">
      <el-table :data="batchJobs">
        <el-table-column prop="drawing_no" label="图号" width="160" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="jobTypes[row.status] || 'info'" effect="light">
              {{ jobLabels[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="error" label="错误" show-overflow-tooltip />
      </el-table>
      <template #footer>
        <el-button @click="progressDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.summary { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.chip {
  display: flex; align-items: baseline; gap: 8px;
  background: #fff; border: 1px solid rgba(226, 232, 240, .9);
  border-radius: 12px; padding: 10px 16px;
  box-shadow: 0 6px 18px rgba(15, 23, 42, .04);
}
.chip span { color: #64748b; font-size: 12px; }
.chip strong { font-size: 20px; letter-spacing: -.02em; }
.table-head { display: flex; justify-content: flex-end; margin-bottom: 12px; }
</style>
