<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Connection, Cpu, Lock, TrendCharts } from '@element-plus/icons-vue'
import api from '../api'
import { useAuthStore } from '../stores/auth'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const auth = useAuthStore()
const { t } = useI18n()
const loading = ref(false)
const wecomMode = ref('mock')

onMounted(async () => {
  try {
    const { data } = await api.get('/auth/config')
    wecomMode.value = data.wecom_mode
  } catch {
    wecomMode.value = 'mock'
  }
})

const users = [
  { name: 'admin', label: '管理员' },
  { name: 'designer', label: '设计员' },
  { name: 'reviewer', label: '审批人' },
  { name: 'viewer', label: '查看者' },
]

const features = [
  { icon: Cpu, title: '参数化出图', text: 'DXF 生成、校验与预览' },
  { icon: Lock, title: '版本与审批', text: '检出锁、审批链、审计留痕' },
  { icon: TrendCharts, title: '数据看板', text: '任务、版本、待审批一屏掌握' },
  { icon: Connection, title: '外部集成', text: '企业微信、ERP、CAD 适配' },
]

async function wecomLogin() {
  if (wecomMode.value === 'real') {
    window.location.href = '/api/auth/wecom/login'
    return
  }
  try {
    const { data } = await api.get('/auth/wecom/login', { params: { user: 'designer' } })
    auth.setSession(data.name, data.role)
    router.push('/drawings')
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function login(name) {
  loading.value = true
  try {
    const { data } = await api.post('/auth/dev-login', { name })
    auth.setSession(data.name, data.role)
    router.push('/drawings')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <section class="hero">
      <div class="brand">
        <div class="mark">C</div>
        <span>CAD Agent Platform</span>
      </div>

      <div class="hero-body">
        <p class="eyebrow">ENGINEERING COLLABORATION</p>
        <h1>让图纸协同<br />更简单一点</h1>
        <p class="lead">
          面向设计团队的一体化工作台：参数化出图、版本审批、审计追踪与 AI 助手。
        </p>

        <div class="features">
          <div v-for="item in features" :key="item.title" class="feature">
            <el-icon><component :is="item.icon" /></el-icon>
            <div>
              <strong>{{ item.title }}</strong>
              <span>{{ item.text }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="hero-foot">内部试点 · v0.23.0</div>
    </section>

    <section class="panel">
      <div class="card">
        <h2>{{ t('login.title') }}</h2>
        <p class="hint">{{ t('login.hint') }}</p>

        <el-button type="primary" class="wecom" @click="wecomLogin">
          {{ t('login.wecom') }}{{ wecomMode === 'mock' ? '（mock）' : '' }}
        </el-button>

        <div class="divider"><span>{{ t('login.divider') }}</span></div>

        <div class="users">
          <el-button
            v-for="u in users"
            :key="u.name"
            :loading="loading"
            class="user-btn"
            @click="login(u.name)"
          >
            {{ t('login.roles.' + u.name) }}（{{ u.name }}）
          </el-button>
        </div>

        <p class="foot">{{ t('login.foot') }}</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.15fr .85fr;
  background: #f4f7fb;
}

.hero {
  position: relative;
  overflow: hidden;
  padding: 48px 56px;
  display: flex;
  flex-direction: column;
  color: #e2e8f0;
  background:
    radial-gradient(900px 500px at 80% 10%, rgba(37, 99, 235, .35), transparent 60%),
    radial-gradient(700px 500px at 10% 90%, rgba(14, 165, 233, .18), transparent 60%),
    linear-gradient(160deg, #0b1220, #111c33 60%, #0b1220);
}

.hero::after {
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(148, 163, 184, .07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, .07) 1px, transparent 1px);
  background-size: 42px 42px;
  pointer-events: none;
}

.brand { display: flex; align-items: center; gap: 10px; font-weight: 700; letter-spacing: .3px; z-index: 1; }
.mark {
  width: 34px; height: 34px; border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6, #22d3ee);
  display: grid; place-items: center; color: #fff; font-weight: 800;
}

.hero-body { margin: auto 0; max-width: 560px; z-index: 1; }
.eyebrow { color: #60a5fa; font-size: 12px; letter-spacing: .22em; margin: 0 0 18px; }
h1 { font-size: clamp(38px, 5vw, 58px); line-height: 1.1; margin: 0 0 20px; letter-spacing: -.03em; }
.lead { color: #94a3b8; font-size: 16px; line-height: 1.8; max-width: 460px; }

.features {
  margin-top: 40px;
  display: grid; grid-template-columns: 1fr 1fr; gap: 14px;
}
.feature {
  display: flex; gap: 10px; align-items: flex-start;
  padding: 12px; border-radius: 12px;
  background: rgba(148, 163, 184, .06);
  border: 1px solid rgba(148, 163, 184, .12);
}
.feature .el-icon { color: #60a5fa; margin-top: 3px; }
.feature strong { display: block; font-size: 13px; color: #e2e8f0; }
.feature span { display: block; font-size: 12px; color: #64748b; margin-top: 3px; }

.hero-foot { z-index: 1; color: #475569; font-size: 12px; }

.panel {
  display: grid; place-items: center;
  padding: 40px;
  background: #f4f7fb;
}

.card {
  width: 100%; max-width: 430px;
  background: #fff;
  border: 1px solid rgba(226, 232, 240, .9);
  border-radius: 20px;
  padding: 36px 34px;
  box-shadow: 0 24px 60px rgba(15, 23, 42, .08);
}
.card h2 { margin: 0 0 8px; font-size: 24px; letter-spacing: -.02em; }
.hint { color: #64748b; font-size: 13px; line-height: 1.6; margin: 0 0 24px; }

.wecom { width: 100%; height: 42px; }

.divider {
  display: flex; align-items: center; gap: 12px;
  color: #94a3b8; font-size: 12px; margin: 22px 0;
}
.divider::before, .divider::after {
  content: ""; flex: 1; height: 1px; background: #e2e8f0;
}

.users { display: flex; flex-direction: column; gap: 10px; }
.user-btn { width: 100%; height: 42px; justify-content: flex-start; padding-left: 18px; }

.foot { margin: 24px 0 0; text-align: center; color: #94a3b8; font-size: 11px; }

@media (max-width: 900px) {
  .login-page { grid-template-columns: 1fr; }
  .hero { padding: 30px 24px 34px; }
  .hero-body { margin: 34px 0; }
  .features { grid-template-columns: 1fr; margin-top: 26px; }
  .hero-foot { display: none; }
  .panel { padding: 26px 16px 40px; }
  .card { padding: 28px 22px; }
}
</style>
