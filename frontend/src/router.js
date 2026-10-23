import { createRouter, createWebHistory } from 'vue-router'

const Login = () => import('./views/Login.vue')
const Drawings = () => import('./views/Drawings.vue')
const DrawingDetail = () => import('./views/DrawingDetail.vue')
const Dashboard = () => import('./views/Dashboard.vue')
const Projects = () => import('./views/Projects.vue')
const Users = () => import('./views/Users.vue')
const Audit = () => import('./views/Audit.vue')
const Images = () => import('./views/Images.vue')
const Assistant = () => import('./views/Assistant.vue')
const Approvals = () => import('./views/Approvals.vue')
const Knowledge = () => import('./views/Knowledge.vue')
const Ops = () => import('./views/Ops.vue')
const NotFound = () => import('./views/NotFound.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/drawings' },
    { path: '/login', component: Login, meta: { title: '登录' } },
    { path: '/drawings', component: Drawings, meta: { title: '图纸' } },
    { path: '/drawings/:id', component: DrawingDetail, meta: { title: '图纸详情' } },
    { path: '/dashboard', component: Dashboard, meta: { title: '运营看板' } },
    { path: '/projects', component: Projects, meta: { title: '项目' } },
    { path: '/users', component: Users, meta: { title: '用户' } },
    { path: '/audit', component: Audit, meta: { title: '审计日志' } },
    { path: '/images', component: Images, meta: { title: 'AI 绘图' } },
    { path: '/assistant', component: Assistant, meta: { title: 'AI 助手' } },
    { path: '/approvals', component: Approvals, meta: { title: '审批待办' } },
    { path: '/knowledge', component: Knowledge, meta: { title: '知识库' } },
    { path: '/ops', component: Ops, meta: { title: '运维' } },
    { path: '/:pathMatch(.*)*', component: NotFound, meta: { title: '未找到' } },
  ],
})

router.beforeEach((to) => {
  if (to.path !== '/login' && !localStorage.getItem('user')) return '/login'
  return true
})

export default router
