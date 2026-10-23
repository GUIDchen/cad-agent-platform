<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import api from '../api'

const route = useRoute()
const { t, locale } = useI18n()
const id = computed(() => route.params.id)
const drawing = ref(null)
const versions = ref([])
const previewUrl = ref('')
const jobStatus = ref('')
const currentJobId = ref('')
const fileInput = ref(null)
const comments = ref([])
const commentText = ref('')
const commentLoading = ref(false)
const diffOpen = ref(false)
const diffRows = ref([])
const diffTitle = ref('')
const role = localStorage.getItem('role')

const statusMap = computed(() => ({
  draft: t('drawings.statuses.draft'),
  generating: t('drawings.statuses.generating'),
  pending_review: t('drawings.statuses.pending_review'),
  approved: t('drawings.statuses.approved'),
  rejected: t('drawings.statuses.rejected'),
  archived: t('drawings.statuses.archived'),
}))

function formatTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString(locale.value === 'en' ? 'en-US' : 'zh-CN')
}

const aiText = ref('')
const aiLoading = ref(false)

const form = reactive({
  length: 180,
  width: 120,
  thickness: 6,
  corner_radius: 0,
  chamfer: 0,
  material: '304',
  surface: '拉丝',
  holes: '[{"x":20,"y":20,"d":6.6},{"x":160,"y":20,"d":6.6},{"x":20,"y":100,"d":6.6},{"x":160,"y":100,"d":6.6}]',
  slots: '[]',
  cutouts: '[]',
  outline: '[]',
})

async function load() {
  drawing.value = (await api.get('/drawings/' + id.value)).data
  versions.value = (await api.get('/drawings/' + id.value + '/versions')).data
  comments.value = (await api.get('/drawings/' + id.value + '/comments')).data
  if (versions.value.length) await showPreview(versions.value[0].id)
}

async function showPreview(versionId) {
  const resp = await api.get('/versions/' + versionId + '/preview', { responseType: 'blob' })
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = URL.createObjectURL(resp.data)
}

async function aiParse() {
  if (!aiText.value) return
  aiLoading.value = true
  try {
    const { data } = await api.post('/ai/parse', { text: aiText.value })
    form.length = data.spec.length
    form.width = data.spec.width
    form.thickness = data.spec.thickness
    form.material = data.spec.material
    form.surface = data.spec.surface
    form.holes = JSON.stringify(data.spec.holes)
    ElMessage.success('已解析（' + data.source + '）')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    aiLoading.value = false
  }
}

async function generate() {
  let holes
  let slots
  let cutouts
  let outline
  try {
    holes = JSON.parse(form.holes)
    slots = JSON.parse(form.slots)
    cutouts = JSON.parse(form.cutouts)
    outline = JSON.parse(form.outline)
  } catch {
    ElMessage.error('孔位/槽位/开口/轮廓必须是 JSON 数组')
    return
  }
  const payload = { ...form, holes, slots, cutouts }
  if (outline.length) payload.outline = outline
  else delete payload.outline
  const { data } = await api.post('/drawings/' + id.value + '/generate', payload)
  currentJobId.value = data.job_id
  jobStatus.value = 'queued'
  watchJob(data.job_id)
}

function watchJob(jobId) {
  if (!window.EventSource) {
    poll(jobId)
    return
  }
  let finished = false
  const source = new EventSource('/api/jobs/' + jobId + '/events')
  source.onmessage = async (event) => {
    const data = JSON.parse(event.data)
    jobStatus.value = data.status
    if (['done', 'failed', 'canceled'].includes(data.status)) {
      finished = true
      source.close()
      if (data.status === 'failed') ElMessage.error(data.error || '生成失败')
      else if (data.status === 'done') ElMessage.success('生成成功')
      await load()
    }
  }
  source.onerror = () => {
    if (!finished) {
      source.close()
      poll(jobId)
    }
  }
}

async function poll(jobId) {
  const timer = setInterval(async () => {
    const { data } = await api.get('/jobs/' + jobId)
    jobStatus.value = data.status
    if (data.status === 'done' || data.status === 'failed') {
      clearInterval(timer)
      if (data.status === 'failed') ElMessage.error(data.error || '生成失败')
      else ElMessage.success('生成成功')
      await load()
    }
  }, 1000)
}

async function cancelJob() {
  if (!currentJobId.value) return
  await api.post('/jobs/' + currentJobId.value + '/cancel')
  jobStatus.value = 'canceled'
  ElMessage.success('已取消')
  await load()
}

async function retryJob() {
  if (!currentJobId.value) return
  const { data } = await api.post('/jobs/' + currentJobId.value + '/retry')
  currentJobId.value = data.job_id
  jobStatus.value = 'queued'
  watchJob(data.job_id)
}

async function approve() {
  await ElMessageBox.confirm('确认通过当前版本？')
  await api.post('/versions/' + versions.value[0].id + '/approve', { comment: 'ok' })
  ElMessage.success('已通过')
  await load()
}

async function reject() {
  const { value } = await ElMessageBox.prompt('驳回原因', '驳回', { inputValidator: (v) => !!v })
  await api.post('/versions/' + versions.value[0].id + '/reject', { comment: value })
  ElMessage.success('已驳回')
  await load()
}

async function download(row) {
  const resp = await api.get('/versions/' + row.id + '/download', { responseType: 'blob' })
  const url = URL.createObjectURL(resp.data)
  const a = document.createElement('a')
  a.href = url
  a.download = 'v' + row.version + '.dxf'
  a.click()
  URL.revokeObjectURL(url)
}

function openDiff(index) {
  const current = versions.value[index]
  const previous = versions.value[index + 1]
  if (!current || !previous) return
  const a = JSON.parse(current.params_json || '{}')
  const b = JSON.parse(previous.params_json || '{}')
  diffRows.value = ['length', 'width', 'thickness', 'material', 'surface', 'holes'].map((key) => ({
    key,
    current: Array.isArray(a[key]) ? JSON.stringify(a[key]) : a[key],
    previous: Array.isArray(b[key]) ? JSON.stringify(b[key]) : b[key],
  }))
  diffTitle.value = 'v' + current.version + ' vs v' + previous.version
  diffOpen.value = true
}

async function postComment() {
  if (!commentText.value.trim()) return
  commentLoading.value = true
  try {
    await api.post('/drawings/' + id.value + '/comments', { body: commentText.value.trim() })
    commentText.value = ''
    comments.value = (await api.get('/drawings/' + id.value + '/comments')).data
    ElMessage.success('已发表评论')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    commentLoading.value = false
  }
}

async function downloadPdf(row) {
  const resp = await api.get('/versions/' + row.id + '/pdf', { responseType: 'blob' })
  const url = URL.createObjectURL(resp.data)
  const a = document.createElement('a')
  a.href = url
  a.download = 'v' + row.version + '.pdf'
  a.click()
  URL.revokeObjectURL(url)
}

function pickFile() {
  fileInput.value?.click()
}

async function uploadFile(file) {
  const form = new FormData()
  form.append('file', file)
  try {
    await api.post('/drawings/' + id.value + '/versions', form)
    ElMessage.success('已上传 ' + file.name)
    await load()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function onFile(event) {
  const file = event.target.files?.[0]
  if (file) await uploadFile(file)
  event.target.value = ''
}

async function onDrop(event) {
  const file = event.dataTransfer?.files?.[0]
  if (file) await uploadFile(file)
}

async function checkout() {
  await api.post('/drawings/' + id.value + '/checkout')
  ElMessage.success('已检出')
  await load()
}

async function exportBom() {
  const resp = await api.get('/drawings/' + id.value + '/bom', { responseType: 'blob' })
  const url = URL.createObjectURL(resp.data)
  const a = document.createElement('a')
  a.href = url
  a.download = drawing.value.drawing_no + '-bom.csv'
  a.click()
  URL.revokeObjectURL(url)
}

async function pushErp() {
  try {
    const { data } = await api.post('/drawings/' + id.value + '/bom/push')
    ElMessage.success('已推送（' + data.mode + '）')
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function checkin() {
  await api.post('/drawings/' + id.value + '/checkin')
  ElMessage.success('已检入')
  await load()
}

onMounted(load)
</script>

<template>
  <div v-if="drawing">
    <h2>{{ drawing.drawing_no }} · {{ drawing.title }}</h2>
    <el-descriptions :column="3" border>
      <el-descriptions-item :label="t('detail.status')">
        <span class="status-dot" :class="'s-' + drawing.status"></span>
        {{ statusMap[drawing.status] || drawing.status || '-' }}
      </el-descriptions-item>
      <el-descriptions-item :label="t('detail.lockedBy')">{{ drawing.locked_by || '-' }}</el-descriptions-item>
      <el-descriptions-item :label="t('detail.versionCount')">{{ versions.length }}</el-descriptions-item>
    </el-descriptions>

    <div class="actions">
      <el-button v-if="role !== 'viewer'" type="primary" @click="checkout">{{ t('detail.checkOut') }}</el-button>
      <el-button v-if="role !== 'viewer'" @click="checkin">{{ t('detail.checkIn') }}</el-button>
      <el-button v-if="role !== 'viewer'" @click="pickFile">{{ t('detail.upload') }}</el-button>
      <input ref="fileInput" type="file" accept=".dxf,.dwg" style="display: none" @change="onFile" />
      <el-button v-if="role === 'reviewer' || role === 'admin'" type="success" @click="approve">{{ t('detail.approve') }}</el-button>
      <el-button v-if="role === 'reviewer' || role === 'admin'" type="danger" @click="reject">{{ t('detail.reject') }}</el-button>
      <el-button v-if="role !== 'viewer'" type="warning" @click="exportBom">{{ t('detail.exportBom') }}</el-button>
      <el-button v-if="role !== 'viewer'" @click="pushErp">{{ t('detail.pushErp') }}</el-button>
    </div>

    <div
      v-if="role !== 'viewer'"
      class="dropzone"
      @dragover.prevent
      @drop.prevent="onDrop"
      @click="pickFile"
    >
      <el-icon><UploadFilled /></el-icon>
      {{ t('detail.dropzone') }}
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :md="10">
        <el-card :header="t('detail.generateCard')">
          <div class="ai">
            <el-input v-model="aiText" type="textarea" :rows="2" :placeholder="t('detail.aiPlaceholder')" />
            <el-button size="small" type="primary" :loading="aiLoading" @click="aiParse">{{ t('detail.aiParse') }}</el-button>
          </div>
          <el-form label-width="70px" size="small">
            <el-form-item :label="t('detail.length')"><el-input-number v-model="form.length" :min="20" /></el-form-item>
            <el-form-item :label="t('detail.width')"><el-input-number v-model="form.width" :min="20" /></el-form-item>
            <el-form-item :label="t('detail.thickness')"><el-input-number v-model="form.thickness" :min="1" /></el-form-item>
            <el-form-item :label="t('detail.cornerRadius')"><el-input-number v-model="form.corner_radius" :min="0" :max="100" /></el-form-item>
            <el-form-item :label="t('detail.chamfer')"><el-input-number v-model="form.chamfer" :min="0" :max="100" /></el-form-item>
            <el-form-item :label="t('detail.material')"><el-input v-model="form.material" /></el-form-item>
            <el-form-item :label="t('detail.surface')"><el-input v-model="form.surface" /></el-form-item>
            <el-form-item :label="t('detail.holes')"><el-input v-model="form.holes" type="textarea" :rows="4" /></el-form-item>
            <el-form-item :label="t('detail.slots')"><el-input v-model="form.slots" type="textarea" :rows="2" /></el-form-item>
            <el-form-item :label="t('detail.cutouts')"><el-input v-model="form.cutouts" type="textarea" :rows="2" /></el-form-item>
            <el-form-item :label="t('detail.outline')"><el-input v-model="form.outline" type="textarea" :rows="2" /></el-form-item>
          </el-form>
          <el-button type="primary" :loading="jobStatus === 'queued' || jobStatus === 'running'" @click="generate">
            {{ t('detail.generate') }}
          </el-button>
          <span class="job">{{ t('detail.task') }}: {{ jobStatus || '-' }}</span>
          <el-button v-if="['queued', 'running'].includes(jobStatus)" size="small" @click="cancelJob">{{ t('detail.cancelJob') }}</el-button>
          <el-button v-if="['failed', 'canceled'].includes(jobStatus)" size="small" @click="retryJob">{{ t('detail.retry') }}</el-button>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="14">
        <el-card :header="t('detail.preview')">
          <img v-if="previewUrl" :src="previewUrl" class="preview" alt="图纸预览" />
          <el-empty v-else :description="t('detail.emptyPreview')" />
        </el-card>
      </el-col>
    </el-row>

    <el-card :header="t('detail.versions')" class="versions">
      <el-table :data="versions">
        <el-table-column prop="version" :label="t('detail.version')" width="80" />
        <el-table-column prop="sha256" label="sha256" width="220" show-overflow-tooltip />
        <el-table-column :label="t('detail.time')">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column :label="t('detail.actions')" width="260">
          <template #default="{ row, $index }">
            <el-button link @click="showPreview(row.id)">{{ t('detail.previewAction') }}</el-button>
            <el-button v-if="$index < versions.length - 1" link @click="openDiff($index)">{{ t('detail.diff') }}</el-button>
            <el-button link @click="downloadPdf(row)">{{ t('detail.pdf') }}</el-button>
            <el-button link @click="download(row)">{{ t('detail.download') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card :header="t('detail.comments')" class="comments">
      <div v-if="comments.length" class="comment-list">
        <div v-for="item in comments" :key="item.id" class="comment">
          <div class="comment-head">
            <strong>{{ item.author_name }}</strong>
            <span>{{ formatTime(item.created_at) }}</span>
          </div>
          <p>{{ item.body }}</p>
        </div>
      </div>
      <el-empty v-else :description="t('detail.emptyComments')" :image-size="70" />
      <div class="comment-form">
        <el-input v-model="commentText" type="textarea" :rows="2" :placeholder="t('detail.commentPlaceholder')" />
        <el-button type="primary" :loading="commentLoading" @click="postComment">{{ t('detail.post') }}</el-button>
      </div>
    </el-card>

    <el-dialog v-model="diffOpen" :title="diffTitle" width="760px">
      <el-table :data="diffRows" size="small">
        <el-table-column prop="key" :label="t('detail.diffField')" width="110" />
        <el-table-column prop="previous" :label="t('detail.diffPrev')" />
        <el-table-column prop="current" :label="t('detail.diffCurrent')" />
      </el-table>
    </el-dialog>
  </div>
</template>

<style scoped>
.actions { margin: 16px 0 10px; display: flex; gap: 8px; flex-wrap: wrap; }
.dropzone {
  margin-bottom: 16px; padding: 14px; border: 1px dashed #bfdbfe; border-radius: 12px;
  background: #f8fbff; color: #475569; font-size: 13px; cursor: pointer;
  display: flex; align-items: center; gap: 8px;
}
.dropzone:hover { border-color: #2563eb; background: #eff6ff; }
.ai { display: flex; gap: 8px; margin-bottom: 12px; align-items: flex-start; }
.preview { width: 100%; border: 1px solid #e2e8f0; }
.versions { margin-top: 16px; }
.comments { margin-top: 16px; }
.comment-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 14px; }
.comment { border-bottom: 1px dashed #e2e8f0; padding-bottom: 8px; }
.comment-head { display: flex; justify-content: space-between; color: #64748b; font-size: 12px; }
.comment p { margin: 6px 0 0; }
.comment-form { display: flex; gap: 8px; align-items: flex-start; }
.job { margin-left: 12px; color: #64748b; }
.status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; background: #94a3b8; }
.status-dot.s-generating, .status-dot.s-pending_review { background: #f59e0b; }
.status-dot.s-approved { background: #10b981; }
.status-dot.s-rejected { background: #ef4444; }
.status-dot.s-draft { background: #94a3b8; }
</style>
