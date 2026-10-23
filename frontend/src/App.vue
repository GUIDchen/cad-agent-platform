<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Bell, Collection, DataLine, Document, Folder, List, MagicStick, Menu, Monitor, Moon, Picture, Sunny, User } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import en from 'element-plus/es/locale/lang/en'
import CommandPalette from './components/CommandPalette.vue'
import api from './api'
import { useAuthStore } from './stores/auth'
import { useNotificationStore } from './stores/notifications'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const notify = useNotificationStore()
const { t, locale: currentLocale } = useI18n()
const elLocale = computed(() => (currentLocale.value === 'en' ? en : zhCn))
const user = computed(() => auth.user)
const role = computed(() => auth.role)
const initial = computed(() => auth.initial)
const notifications = computed(() => notify.items)
const unread = computed(() => notify.unread)
const drawer = ref(false)
const theme = ref(localStorage.getItem('theme') || 'light')

let timer = null

function applyTheme() {
  document.documentElement.dataset.theme = theme.value
}

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  localStorage.setItem('theme', theme.value)
  applyTheme()
}

function toggleLocale() {
  currentLocale.value = currentLocale.value === 'zh' ? 'en' : 'zh'
  localStorage.setItem('locale', currentLocale.value)
  document.documentElement.lang = currentLocale.value === 'en' ? 'en' : 'zh-CN'
}

onMounted(() => {
  applyTheme()
  notify.load()
  timer = setInterval(() => notify.load(), 60000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

watch(() => route.fullPath, () => {
  drawer.value = false
  notify.load()
})

async function openNotification(item) {
  if (!item.read) await notify.markRead(item.id)
  if (item.link) router.push(item.link)
}

async function readAll() {
  await notify.readAll()
}

const isLogin = computed(() => route.path === '/login')
const title = computed(() => {
  if (route.path.startsWith('/drawings/')) return t('nav.drawingDetail')
  const map = {
    '/drawings': 'nav.drawings',
    '/projects': 'nav.projects',
    '/dashboard': 'nav.dashboard',
    '/approvals': 'nav.approvals',
    '/images': 'nav.images',
    '/assistant': 'nav.assistant',
    '/users': 'nav.users',
    '/audit': 'nav.audit',
    '/knowledge': 'nav.knowledge',
    '/ops': 'nav.ops',
  }
  return t(map[route.path] || 'nav.drawings')
})

const menu = computed(() => {
  const items = [
    { path: '/drawings', label: t('nav.drawings'), icon: Document },
    { path: '/projects', label: t('nav.projects'), icon: Folder },
    { path: '/dashboard', label: t('nav.dashboard'), icon: DataLine },
    { path: '/images', label: t('nav.images'), icon: Picture },
    { path: '/assistant', label: t('nav.assistant'), icon: MagicStick },
    { path: '/knowledge', label: t('nav.knowledge'), icon: Collection },
  ]
  if (role.value === 'reviewer' || role.value === 'admin') {
    items.push({ path: '/approvals', label: t('nav.approvals'), icon: List })
  }
  if (role.value === 'admin') {
    items.push({ path: '/users', label: t('nav.users'), icon: User })
    items.push({ path: '/audit', label: t('nav.audit'), icon: List })
    items.push({ path: '/ops', label: t('nav.ops'), icon: Monitor })
  }
  return items
})

async function logout() {
  try {
    await api.post('/auth/logout')
  } catch {}
  auth.clear()
  router.push('/login')
}

function onCommand(command) {
  if (command === 'logout') logout()
}
</script>

<template>
  <el-config-provider :locale="elLocale">
  <router-view v-if="isLogin" />

  <div v-else class="shell">
    <aside class="sidebar" :class="{ open: drawer }">
      <div class="logo">
        <div class="logo-mark">C</div>
        <div>
          <div class="logo-title">CAD Agent</div>
          <div class="logo-sub">图纸协同平台</div>
        </div>
      </div>

      <nav class="menu">
        <router-link
          v-for="item in menu"
          :key="item.path"
          :to="item.path"
          class="menu-item"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="side-foot">v0.62.0 · 内网试点</div>
    </aside>

    <div v-if="drawer" class="overlay" @click="drawer = false" />

    <div class="main">
      <header class="topbar">
        <button class="icon-btn" @click="drawer = !drawer" aria-label="打开菜单">
          <el-icon><Menu /></el-icon>
        </button>
        <div class="crumb">
          <span>{{ t('shell.workspace') }}</span>
          <i>/</i>
          <strong>{{ title }}</strong>
        </div>
        <div class="right">
          <button class="icon-btn lang" :aria-label="t('shell.language')" @click="toggleLocale">
            {{ currentLocale === 'zh' ? 'EN' : '中' }}
          </button>
          <button class="icon-btn theme" :aria-label="theme === 'dark' ? t('shell.themeLight') : t('shell.themeDark')" @click="toggleTheme">
            <el-icon><Sunny v-if="theme === 'dark'" /><Moon v-else /></el-icon>
          </button>
          <el-popover placement="bottom-end" :width="330" trigger="click">
            <template #reference>
              <button class="icon-btn bell" :aria-label="t('shell.notifications')">
                <el-icon><Bell /></el-icon>
                <span v-if="unread" class="badge">{{ unread }}</span>
              </button>
            </template>
            <div class="notif-head">
              <strong>{{ t('shell.notifications') }}</strong>
              <el-button link size="small" @click="readAll">{{ t('shell.readAll') }}</el-button>
            </div>
            <div v-if="notifications.length" class="notif-list">
              <div
                v-for="item in notifications"
                :key="item.id"
                class="notif"
                :class="{ unread: !item.read }"
                @click="openNotification(item)"
              >
                <strong>{{ item.title }}</strong>
                <p v-if="item.body">{{ item.body }}</p>
                <span>{{ item.created_at }}</span>
              </div>
            </div>
            <el-empty v-else :description="t('shell.empty')" :image-size="60" />
          </el-popover>
          <el-tag effect="plain" round>{{ user }}</el-tag>
          <el-dropdown @command="onCommand">
            <span class="avatar">{{ initial }}</span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">{{ t('shell.logout') }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="content">
        <router-view />
      </main>
    </div>
  </div>

  <CommandPalette v-if="!isLogin" />
  </el-config-provider>
</template>

<style scoped>
.shell { min-height: 100vh; }

.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  width: 232px;
  background: linear-gradient(180deg, var(--sidebar), var(--sidebar-2));
  color: #cbd5e1;
  display: flex;
  flex-direction: column;
  padding: 22px 16px;
  z-index: 30;
}

.logo { display: flex; align-items: center; gap: 10px; padding: 4px 8px 22px; }
.logo-mark {
  width: 36px; height: 36px; border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6, #22d3ee);
  display: grid; place-items: center;
  font-weight: 800; color: #fff; font-size: 18px;
}
.logo-title { color: #f8fafc; font-weight: 700; letter-spacing: .3px; }
.logo-sub { font-size: 11px; color: #64748b; margin-top: 2px; }

.menu { display: flex; flex-direction: column; gap: 4px; flex: 1; }
.menu-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: 10px;
  color: #94a3b8; text-decoration: none; font-size: 14px;
  transition: background .15s, color .15s;
}
.menu-item:hover { background: rgba(148, 163, 184, .1); color: #e2e8f0; }
.menu-item.router-link-active {
  background: linear-gradient(90deg, rgba(37, 99, 235, .28), rgba(37, 99, 235, .08));
  color: #fff;
  box-shadow: inset 3px 0 0 #60a5fa;
}
.side-foot { font-size: 11px; color: #475569; padding: 12px 10px 0; }

.main { margin-left: 232px; min-height: 100vh; display: flex; flex-direction: column; }

.topbar {
  height: 64px; position: sticky; top: 0; z-index: 20;
  display: flex; align-items: center; gap: 16px;
  padding: 0 28px;
  background: rgba(244, 247, 251, .86);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(226, 232, 240, .8);
}
.crumb { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 13px; flex: 1; }
.crumb i { font-style: normal; color: #cbd5e1; }
.crumb strong { color: var(--ink); font-weight: 600; }

.right { display: flex; align-items: center; gap: 12px; }
.avatar {
  width: 34px; height: 34px; border-radius: 50%;
  display: grid; place-items: center; cursor: pointer;
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  color: #1d4ed8; font-weight: 700; font-size: 13px;
}

.content { flex: 1; min-width: 0; }

.icon-btn {
  display: none;
  border: 1px solid var(--line); background: #fff;
  width: 36px; height: 36px; border-radius: 10px;
  align-items: center; justify-content: center; cursor: pointer;
}
.bell { display: inline-flex; position: relative; }
.theme { display: inline-flex; }
.lang { display: inline-flex; width: auto; padding: 0 8px; font-size: 12px; font-weight: 700; }
.badge {
  position: absolute; top: -4px; right: -4px; min-width: 16px; height: 16px;
  padding: 0 4px; border-radius: 999px; background: #ef4444; color: #fff;
  font-size: 10px; line-height: 16px; text-align: center;
}
.notif-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.notif-list { max-height: 360px; overflow: auto; }
.notif { padding: 8px 6px; border-bottom: 1px solid #f1f5f9; cursor: pointer; }
.notif:hover { background: #f8fafc; }
.notif.unread { background: #eff6ff; }
.notif strong { display: block; font-size: 13px; }
.notif p { margin: 3px 0; color: #475569; font-size: 12px; }
.notif span { color: #94a3b8; font-size: 11px; }

.overlay { display: none; }

@media (max-width: 900px) {
  .sidebar { transform: translateX(-100%); transition: transform .2s ease; }
  .sidebar.open { transform: translateX(0); }
  .main { margin-left: 0; }
  .topbar { padding: 0 14px; }
  .icon-btn { display: inline-flex; }
  .overlay {
    display: block; position: fixed; inset: 0;
    background: rgba(15, 23, 42, .35); z-index: 25;
  }
}
</style>
