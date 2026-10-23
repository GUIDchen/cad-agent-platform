<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const open = ref(false)
const query = ref('')
const active = ref(0)
const drawings = ref([])
const input = ref(null)

const routes = [
  { path: '/drawings', label: '图纸', hint: '列表' },
  { path: '/projects', label: '项目', hint: '成员与项目' },
  { path: '/dashboard', label: '看板', hint: 'KPI 与图表' },
  { path: '/approvals', label: '审批待办', hint: 'reviewer' },
  { path: '/knowledge', label: '知识库', hint: '工艺检索' },
  { path: '/images', label: 'AI 绘图', hint: '提示词出图' },
  { path: '/assistant', label: 'AI 助手', hint: '工具调用' },
  { path: '/users', label: '用户', hint: 'admin' },
  { path: '/audit', label: '审计', hint: 'admin' },
]

const items = computed(() => {
  const q = query.value.trim().toLowerCase()
  const matchedRoutes = routes
    .filter((item) => !q || item.label.toLowerCase().includes(q) || item.path.includes(q))
    .map((item) => ({ ...item, type: 'route', key: item.path }))
  const matchedDrawings = drawings.value
    .filter((item) => !q || item.drawing_no.toLowerCase().includes(q) || (item.title || '').toLowerCase().includes(q))
    .map((item) => ({
      type: 'drawing',
      key: 'drawing-' + item.id,
      id: item.id,
      label: item.drawing_no,
      hint: item.title,
      path: '/drawings/' + item.id,
    }))
  return [...matchedRoutes, ...matchedDrawings].slice(0, 10)
})

watch(query, () => {
  active.value = 0
})

function show() {
  open.value = true
  query.value = ''
  active.value = 0
  loadDrawings()
  nextTick(() => input.value?.focus())
}

function close() {
  open.value = false
}

function onKey(event) {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault()
    show()
    return
  }
  if (event.key === 'Escape') close()
}

async function loadDrawings() {
  try {
    drawings.value = (await api.get('/drawings', { params: { limit: 50 } })).data
  } catch {
    drawings.value = []
  }
}

function go(item) {
  close()
  router.push(item.path)
}

function onEnter() {
  const item = items.value[active.value]
  if (item) go(item)
}

onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="palette-overlay" @click.self="close">
      <div class="palette">
        <input
          ref="input"
          v-model="query"
          placeholder="搜索页面、图号、名称…  (Ctrl/Cmd + K)"
          @keydown.down.prevent="active = (active + 1) % Math.max(items.length, 1)"
          @keydown.up.prevent="active = (active - 1 + Math.max(items.length, 1)) % Math.max(items.length, 1)"
          @keydown.enter.prevent="onEnter"
        />
        <div class="palette-list">
          <div
            v-for="(item, index) in items"
            :key="item.key"
            class="palette-item"
            :class="{ active: index === active }"
            @click="go(item)"
            @mouseenter="active = index"
          >
            <span>{{ item.label }}</span>
            <small>{{ item.hint }}</small>
          </div>
          <div v-if="!items.length" class="palette-empty">没有匹配结果</div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.palette-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(15, 23, 42, .35);
  display: flex; justify-content: center; align-items: flex-start;
  padding-top: 12vh;
}
.palette {
  width: min(640px, calc(100vw - 32px));
  background: #fff; border-radius: 14px;
  box-shadow: 0 30px 80px rgba(15, 23, 42, .25);
  overflow: hidden;
}
.palette input {
  width: 100%; border: 0; outline: 0;
  padding: 16px 18px; font-size: 15px;
  border-bottom: 1px solid #e2e8f0;
}
.palette-list { max-height: 360px; overflow: auto; padding: 6px; }
.palette-item {
  display: flex; justify-content: space-between; gap: 12px;
  padding: 10px 12px; border-radius: 8px; cursor: pointer;
}
.palette-item.active { background: #eff6ff; }
.palette-item span { font-weight: 600; }
.palette-item small { color: #64748b; }
.palette-empty { padding: 18px; color: #94a3b8; text-align: center; }
</style>
