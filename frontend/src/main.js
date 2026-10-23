import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'
import 'element-plus/theme-chalk/base.css'
import 'element-plus/theme-chalk/el-message.css'
import 'element-plus/theme-chalk/el-message-box.css'
import 'element-plus/theme-chalk/el-loading.css'
import './styles.css'
import App from './App.vue'
import router from './router'
import i18n from './i18n'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30000, retry: 1, refetchOnWindowFocus: false },
  },
})

createApp(App)
  .use(createPinia())
  .use(i18n)
  .use(VueQueryPlugin, { queryClient })
  .use(router)
  .mount('#app')
